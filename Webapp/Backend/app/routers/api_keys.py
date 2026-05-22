from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
import secrets
import hashlib

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth/api-keys", tags=["api-keys"])
limiter = Limiter(key_func=get_remote_address)

class APIKeyCreate(BaseModel):
    name: str


def _hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256 for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


@router.post("")
@limiter.limit("10/minute")
async def create_api_key(
    request: Request,
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key for desktop agent authentication"""

    # Generate secure API key
    api_key = f"mba_{secrets.token_urlsafe(32)}"

    # Hash the key before storing in database
    api_key_hash = _hash_api_key(api_key)
    current_user.api_key_hash = api_key_hash
    db.commit()

    return {
        "id": current_user.id,
        "name": key_data.name,
        "api_key": api_key,
        "created_at": current_user.updated_at.isoformat()
    }


@router.get("")
@limiter.limit("10/minute")
async def get_api_key(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's API key info (not the full key)"""

    if not current_user.api_key_hash:
        return {"has_api_key": False}

    # Show preview - the actual key starts with "mba_"
    return {
        "has_api_key": True,
        "key_prefix": "mba_...",
        "created_at": current_user.updated_at.isoformat()
    }


@router.delete("")
@limiter.limit("10/minute")
async def revoke_api_key(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke the current API key"""

    current_user.api_key_hash = None
    db.commit()

    return {"message": "API key revoked successfully"}