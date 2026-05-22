from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional
import hashlib
from app.database import get_db
from app.models.user import User
from app.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


def _hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256 for secure storage/comparison."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user via JWT token or API key.

    Supports two authentication methods:
    1. JWT Bearer token (for web frontend)
    2. X-API-Key header (for desktop agent)
    """

    # Try API key first (using hashed comparison)
    if x_api_key:
        key_hash = _hash_api_key(x_api_key)
        user = db.query(User).filter(User.api_key_hash == key_hash).first()
        if user:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    # Try JWT token
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user