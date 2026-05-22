from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from datetime import datetime, UTC

from app.database import Base


def _utcnow():
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    google_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)

    google_credentials = Column(Text, nullable=False)
    drive_folder_id = Column(String, nullable=True)

    auto_cleanup_enabled = Column(Boolean, default=True)
    max_backups_per_world = Column(Integer, default=10)

    refresh_token = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    last_login = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    worlds = relationship("World", back_populates="user", cascade="all, delete-orphan")


class World(Base):
    __tablename__ = "worlds"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    local_path = Column(String, nullable=True)

    drive_folder_id = Column(String, nullable=True)

    auto_sync_enabled = Column(Boolean, default=False)
    sync_interval_minutes = Column(Integer, default=60)
    last_sync = Column(DateTime, nullable=True)

    total_backups = Column(Integer, default=0)
    total_size_mb = Column(Float, default=0.0)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="worlds")
    backups = relationship("Backup", back_populates="world", cascade="all, delete-orphan")


class Backup(Base):
    __tablename__ = "backups"

    id = Column(Integer, primary_key=True, index=True)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)

    drive_file_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)

    size_mb = Column(Float, nullable=False)
    compressed = Column(Boolean, default=True)

    backup_type = Column(String, default="manual")
    status = Column(String, default="completed")
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_utcnow)

    world = relationship("World", back_populates="backups")


class PairingCode(Base):
    __tablename__ = "pairing_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String, index=True, nullable=False)
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")
