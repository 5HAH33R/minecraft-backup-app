from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
import secrets
import hashlib
import base64

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.google_drive_service import GoogleDriveService
from app.utils.encryption import encrypt_credentials, decrypt_credentials
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

# Store state temporarily (in production, use Redis)
# For now, we'll use a simple dict (will be lost on server restart)
pending_auth_states = {}

# Google OAuth config
GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
    }
}

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token for authenticated users.

    Args:
        data: Dictionary containing token claims (e.g., user ID).

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def generate_code_verifier() -> str:
    """
    Generate a PKCE code verifier for OAuth authorization.

    Returns:
        URL-safe base64-encoded random string.
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8')
    return code_verifier.rstrip('=')


def generate_code_challenge(verifier: str) -> str:
    """
    Generate a PKCE code challenge from a verifier using SHA-256.

    Args:
        verifier: The PKCE code verifier string.

    Returns:
        URL-safe base64-encoded SHA-256 hash of the verifier.
    """
    digest = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(digest).decode('utf-8')
    return challenge.rstrip('=')

@router.get("/google/login")
@limiter.limit("10/minute")
async def google_login(request: Request):
    """
    Initiate Google OAuth 2.0 authorization flow with PKCE.

    Generates secure OAuth parameters including code verifier and challenge,
    then returns the Google authorization URL for the frontend to redirect to.
    The state and verifier are stored temporarily for validation on callback.
    """
    
    # Generate PKCE parameters
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(32)
    
    # Store code_verifier with state for later use
    pending_auth_states[state] = {
        'code_verifier': code_verifier,
        'timestamp': datetime.utcnow()
    }
    
    # Build authorization URL with PKCE
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope={settings.google_scopes_string}&"
        f"state={state}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return {"auth_url": auth_url}

@router.get("/google/callback")
@limiter.limit("10/minute")
async def google_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    """
    Handle Google OAuth 2.0 callback with PKCE verification.

    Validates the state parameter and code verifier, exchanges the authorization
    code for tokens, retrieves user profile information, creates or updates the
    user record in the database, and redirects to the frontend with a JWT token.
    """
    
    # Verify state and get code_verifier
    if state not in pending_auth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    auth_data = pending_auth_states[state]
    code_verifier = auth_data['code_verifier']
    
    # Clean up state (remove from memory)
    del pending_auth_states[state]
    
    # Exchange code for tokens with PKCE
    import httpx
    
    token_data = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'code': code,
        'code_verifier': code_verifier,
        'grant_type': 'authorization_code',
        'redirect_uri': settings.GOOGLE_REDIRECT_URI
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            'https://oauth2.googleapis.com/token',
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
    
    if token_response.status_code != 200:
        error_detail = token_response.json()
        raise HTTPException(
            status_code=400,
            detail=f"Token exchange failed: {error_detail.get('error_description', 'Unknown error')}"
        )
    
    tokens = token_response.json()
    
    # Get user info
    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f"Bearer {tokens['access_token']}"}
        )
    
    if user_info_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info")
    
    user_info = user_info_response.json()
    
    # Prepare credentials dict
    credentials_dict = {
        'token': tokens['access_token'],
        'refresh_token': tokens.get('refresh_token'),
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': settings.GOOGLE_CLIENT_ID,
        'client_secret': settings.GOOGLE_CLIENT_SECRET,
        'scopes': settings.GOOGLE_SCOPES
    }
    
    # Initialize Drive service
    drive_service = GoogleDriveService(credentials_dict)
    
    email = user_info.get('email')
    google_id = user_info.get('id')
    display_name = user_info.get('name')
    profile_picture = user_info.get('picture')
    
    # Encrypt credentials
    encrypted_credentials = encrypt_credentials(json.dumps(credentials_dict))
    
    # Create or update user
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if not user:
        # Create main app folder in user's Drive
        try:
            folder_id = drive_service.create_app_folder()
        except Exception as e:
            print(f"Error creating Drive folder: {e}")
            folder_id = None
        
        user = User(
            email=email,
            google_id=google_id,
            display_name=display_name,
            profile_picture=profile_picture,
            google_credentials=encrypted_credentials,
            drive_folder_id=folder_id
        )
        db.add(user)
    else:
        # Update credentials and last login
        user.google_credentials = encrypted_credentials
        user.last_login = datetime.utcnow()
        user.display_name = display_name
        user.profile_picture = profile_picture
    
    db.commit()
    db.refresh(user)
    
    # Generate refresh token for desktop agent auto-refresh
    refresh_token_raw = secrets.token_urlsafe(48)
    user.refresh_token = encrypt_credentials(refresh_token_raw)
    db.commit()

    # Create JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Redirect to frontend with token and refresh token
    frontend_url = settings.ALLOWED_ORIGINS.split(",")[0]
    redirect_url = (
        f"{frontend_url}/auth/callback"
        f"?token={access_token}"
        f"&refresh_token={refresh_token_raw}"
    )

    return RedirectResponse(url=redirect_url)

@router.get("/me")
@limiter.limit("10/minute")
async def get_current_user_info(request: Request, current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.

    Returns the user's profile data including ID, email, display name,
    profile picture, and login timestamps. Requires valid JWT authentication.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "profile_picture": current_user.profile_picture,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None
    }


@router.post("/logout")
@limiter.limit("10/minute")
async def logout(request: Request, current_user: User = Depends(get_current_user)):
    """
    Log out the current user.

    Note: This endpoint does not invalidate the JWT token server-side.
    The client must delete the token from local storage. This endpoint
    primarily confirms the logout action was received.
    """
    return {"message": "Logged out successfully"}