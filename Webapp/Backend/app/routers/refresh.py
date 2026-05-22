"""Refresh token endpoint for desktop agent auto-refresh."""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
import json

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.utils.encryption import decrypt_credentials
from app.routers.auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


class RefreshRequest(BaseModel):
    """Request body for token refresh."""
    refresh_token: str


@router.post("/refresh")
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new JWT access token.

    Looks up the user by iterating over stored refresh tokens (decrypted),
    verifies the token matches, and issues a fresh access token.

    Rate limited to 10 requests per minute.
    """
    if not body.refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token is required")

    # Iterate users to find matching refresh token
    user = None
    for candidate in db.query(User).filter(User.refresh_token.isnot(None)).all():
        try:
            stored_token = decrypt_credentials(candidate.refresh_token)
            if stored_token == body.refresh_token:
                user = candidate
                break
        except Exception:
            continue

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    # Issue new access token
    new_access_token = create_access_token(data={"sub": str(user.id)})

    return {"access_token": new_access_token}
