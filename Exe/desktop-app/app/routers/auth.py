from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
from jose import jwt
import secrets
import hashlib
import base64
import json
import httpx

from app.config import get_settings
from app.database import get_db
from app.models import User, World, Backup
from app.encryption import encrypt_credentials, decrypt_credentials
from app.dependencies import get_current_user
from app.services.google_drive_service import GoogleDriveService

router = APIRouter(tags=["auth"])
settings = get_settings()

# In-memory OAuth state store with age-based cleanup
pending_auth_states: dict = {}
_AUTH_STATE_TTL = 300  # 5 minutes


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")


def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


@router.get("/auth/login")
async def google_login():
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    state = secrets.token_urlsafe(32)

    pending_auth_states[state] = {
        "code_verifier": code_verifier,
        "timestamp": datetime.now(UTC),
    }

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


@router.get("/auth/google/callback")
async def google_callback(code: str, state: str, db: Session = Depends(get_db)):
    if state not in pending_auth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    auth_data = pending_auth_states.pop(state)
    code_verifier = auth_data["code_verifier"]

    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if token_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Token exchange failed")

    tokens = token_resp.json()

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )

    if user_resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get user info")

    user_info = user_resp.json()

    credentials_dict = {
        "token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "scopes": settings.GOOGLE_SCOPES,
    }

    drive_service = GoogleDriveService(credentials_dict)

    email = user_info.get("email")
    google_id = user_info.get("id")
    display_name = user_info.get("name")
    profile_picture = user_info.get("picture")

    encrypted_credentials = encrypt_credentials(json.dumps(credentials_dict))

    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        try:
            folder_id = drive_service.create_app_folder()
        except Exception:
            folder_id = None

        user = User(
            email=email,
            google_id=google_id,
            display_name=display_name,
            profile_picture=profile_picture,
            google_credentials=encrypted_credentials,
            drive_folder_id=folder_id,
        )
        db.add(user)
    else:
        user.google_credentials = encrypted_credentials
        user.last_login = datetime.now(UTC)
        user.display_name = display_name
        user.profile_picture = profile_picture

    db.commit()
    db.refresh(user)

    refresh_token_raw = secrets.token_urlsafe(48)
    user.refresh_token = encrypt_credentials(refresh_token_raw)
    db.commit()

    access_token = create_access_token(data={"sub": str(user.id)})

    redirect_url = f"/?token={access_token}&refresh_token={refresh_token_raw}"
    return RedirectResponse(url=redirect_url)


@router.get("/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "profile_picture": current_user.profile_picture,
        "auto_cleanup_enabled": current_user.auto_cleanup_enabled,
        "max_backups_per_world": current_user.max_backups_per_world,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
    }


@router.patch("/auth/preferences")
async def update_preferences(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if "auto_cleanup_enabled" in body:
        current_user.auto_cleanup_enabled = bool(body["auto_cleanup_enabled"])
    if "max_backups_per_world" in body:
        current_user.max_backups_per_world = int(body["max_backups_per_world"])
    db.commit()

    # Run cleanup immediately if auto-cleanup is enabled
    if current_user.auto_cleanup_enabled and current_user.max_backups_per_world > 0:
        worlds = db.query(World).filter(World.user_id == current_user.id).all()
        for world in worlds:
            backups = (
                db.query(Backup)
                .filter(Backup.world_id == world.id, Backup.status == "completed")
                .order_by(Backup.created_at.desc())
                .all()
            )
            if len(backups) > current_user.max_backups_per_world:
                excess = backups[current_user.max_backups_per_world:]
                creds_json = decrypt_credentials(current_user.google_credentials)
                drive = GoogleDriveService(json.loads(creds_json))
                for b in excess:
                    try:
                        drive.delete_backup(b.drive_file_id)
                    except Exception:
                        pass
                    db.delete(b)
                db.commit()

    return {"message": "Preferences updated"}


@router.post("/auth/logout")
async def logout(current_user: User = Depends(get_current_user)):
    return {"message": "Logged out successfully"}


@router.post("/auth/refresh")
async def refresh_token(body: dict, db: Session = Depends(get_db)):
    refresh_token_str = body.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    user = None
    for candidate in db.query(User).filter(User.refresh_token.isnot(None)).all():
        try:
            stored = decrypt_credentials(candidate.refresh_token)
            if stored == refresh_token_str:
                user = candidate
                break
        except Exception:
            continue

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": new_token}
