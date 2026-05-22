"""Pairing code endpoints for desktop agent device pairing flow."""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime, timedelta
import secrets
import string
import hashlib

from app.database import get_db
from app.models.user import User
from app.models.pairing_code import PairingCode
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth/pair", tags=["pairing"])
limiter = Limiter(key_func=get_remote_address)


class ExchangeRequest(BaseModel):
    code: str


def _generate_pairing_code() -> str:
    """Generate a 6-character alphanumeric pairing code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))


def _hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256 for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


@router.post("")
@limiter.limit("10/minute")
async def create_pairing_code(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a 6-character pairing code valid for 5 minutes.

    JWT-protected — called from the frontend Settings page.
    The user types this code into the desktop agent's --pair flag.
    """
    # Invalidate any existing unused non-expired codes for this user
    existing = db.query(PairingCode).filter(
        PairingCode.user_id == current_user.id,
        PairingCode.used == False,
        PairingCode.expires_at > datetime.utcnow(),
    ).all()
    for code in existing:
        code.used = True
    db.commit()

    code_str = _generate_pairing_code()
    pairing_code = PairingCode(
        user_id=current_user.id,
        code=code_str,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.add(pairing_code)
    db.commit()
    db.refresh(pairing_code)

    return {
        "code": code_str,
        "expires_at": pairing_code.expires_at.isoformat(),
    }


@router.post("/exchange")
@limiter.limit("10/minute")
async def exchange_pairing_code(
    request: Request,
    body: ExchangeRequest,
    db: Session = Depends(get_db),
):
    """Exchange a pairing code for a permanent API key.

    No auth required — called by the desktop agent with just the code.
    The code must be valid, not expired, and not already used.
    """
    if not body.code or len(body.code) != 6:
        raise HTTPException(status_code=400, detail="Invalid pairing code")

    code_entry = db.query(PairingCode).filter(
        PairingCode.code == body.code.upper(),
        PairingCode.used == False,
    ).first()

    if not code_entry:
        raise HTTPException(status_code=404, detail="Pairing code not found")

    if code_entry.expires_at < datetime.utcnow():
        code_entry.used = True
        db.commit()
        raise HTTPException(status_code=410, detail="Pairing code has expired")

    user = db.query(User).filter(User.id == code_entry.user_id).first()
    if not user:
        code_entry.used = True
        db.commit()
        raise HTTPException(status_code=404, detail="User not found")

    # Generate API key
    api_key = f"mba_{secrets.token_urlsafe(32)}"
    api_key_hash = _hash_api_key(api_key)
    user.api_key_hash = api_key_hash

    # Mark code as used
    code_entry.used = True
    db.commit()

    return {"api_key": api_key}


@router.get("/status")
@limiter.limit("10/minute")
async def pairing_status(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check whether the current user has an API key set.

    Polled by the frontend to detect when a desktop agent has
    successfully exchanged a pairing code.
    """
    return {
        "paired": current_user.api_key_hash is not None,
        "has_api_key": current_user.api_key_hash is not None,
    }
