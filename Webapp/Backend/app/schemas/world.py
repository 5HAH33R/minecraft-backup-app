"""World-related Pydantic schemas for request/response validation."""
from typing import Optional
from pydantic import BaseModel, Field


class WorldCreate(BaseModel):
    """
    Schema for creating a new world.

    Attributes:
        name: The name of the Minecraft world.
        description: Optional description for the world.
        local_path: Optional path to the world files on local disk.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Name of the world")
    description: Optional[str] = Field(None, max_length=1000, description="World description")
    local_path: Optional[str] = Field(None, description="Local path to world files")


class WorldUpdate(BaseModel):
    """
    Schema for updating an existing world.

    All fields are optional - only provided fields will be updated.

    Attributes:
        name: New name for the world.
        description: New description for the world.
        local_path: New local path for the world files.
        auto_sync_enabled: Enable or disable automatic sync for this world.
        sync_interval_minutes: Interval in minutes between automatic syncs.
    """
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    local_path: Optional[str] = None
    auto_sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = Field(None, ge=5, le=1440)


class WorldResponse(BaseModel):
    """
    Schema for world response data.

    Attributes:
        id: Unique identifier for the world.
        name: Name of the world.
        description: Description of the world.
        local_path: Local path to world files.
        auto_sync_enabled: Whether automatic sync is enabled.
        sync_interval_minutes: Sync interval in minutes.
        last_sync: ISO timestamp of last sync.
        total_backups: Number of backups stored.
        total_size_mb: Total size of backups in MB.
        created_at: ISO timestamp when world was created.
        updated_at: ISO timestamp when world was last updated.
    """
    id: int
    name: str
    description: Optional[str]
    local_path: Optional[str]
    auto_sync_enabled: bool
    sync_interval_minutes: Optional[int]
    last_sync: Optional[str]
    total_backups: int
    total_size_mb: float
    created_at: str
    updated_at: str


class BackupResponse(BaseModel):
    """
    Schema for backup response data.

    Attributes:
        id: Unique identifier for the backup.
        filename: Name of the backup file.
        size_mb: Size of the backup in MB.
        backup_type: Type of backup (manual, scheduled, etc.).
        status: Current status of the backup.
        created_at: ISO timestamp when backup was created.
        drive_file_id: Google Drive file ID for the backup.
    """
    id: int
    filename: str
    size_mb: float
    backup_type: str
    status: str
    created_at: str
    drive_file_id: Optional[str] = None