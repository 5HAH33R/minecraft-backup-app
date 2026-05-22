from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    google_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)

    # Google Drive credentials (encrypted)
    google_credentials = Column(Text, nullable=False)
    drive_folder_id = Column(String, nullable=True)

    # API Key hash for desktop agent (alternative to JWT)
    # Stored as SHA-256 hash for security
    api_key_hash = Column(String, unique=True, index=True, nullable=True)

    # Settings
    auto_cleanup_enabled = Column(Boolean, default=True)
    max_backups_per_world = Column(Integer, default=10)

    # Refresh token for desktop agent auto-refresh
    refresh_token = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    worlds = relationship("World", back_populates="user", cascade="all, delete-orphan")

class World(Base):
    __tablename__ = "worlds"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # World info
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    local_path = Column(String, nullable=True)
    
    # Google Drive info
    drive_folder_id = Column(String, nullable=True)
    
    # Sync settings
    auto_sync_enabled = Column(Boolean, default=False)
    sync_interval_minutes = Column(Integer, default=60)
    last_sync = Column(DateTime, nullable=True)
    
    # Statistics
    total_backups = Column(Integer, default=0)
    total_size_mb = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="worlds")
    backups = relationship("Backup", back_populates="world", cascade="all, delete-orphan")

class Backup(Base):
    __tablename__ = "backups"
    
    id = Column(Integer, primary_key=True, index=True)
    world_id = Column(Integer, ForeignKey("worlds.id"), nullable=False)
    
    # Google Drive info
    drive_file_id = Column(String, unique=True, index=True, nullable=False)
    filename = Column(String, nullable=False)
    
    # File info
    size_mb = Column(Float, nullable=False)
    compressed = Column(Boolean, default=True)
    
    # Metadata
    backup_type = Column(String, default="manual")
    status = Column(String, default="completed")
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    world = relationship("World", back_populates="backups")