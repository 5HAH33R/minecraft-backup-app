from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from slowapi import Limiter
from slowapi.util import get_remote_address
import shutil
from pathlib import Path
import tempfile

from app.database import get_db
from app.models.user import User, World
from app.dependencies import get_current_user
from app.config import get_settings
from app.schemas.world import WorldCreate, WorldUpdate, WorldResponse

router = APIRouter(prefix="/api/worlds", tags=["worlds"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

@router.get("")
@limiter.limit("100/minute")
async def list_worlds(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all worlds for the current user.

    Returns a list of all Minecraft worlds associated with the authenticated user,
    including sync status, backup counts, and sizes.
    """
    worlds = db.query(World).filter(World.user_id == current_user.id).all()
    
    return [{
        "id": w.id,
        "name": w.name,
        "description": w.description,
        "local_path": w.local_path,
        "auto_sync_enabled": w.auto_sync_enabled,
        "sync_interval_minutes": w.sync_interval_minutes,
        "last_sync": w.last_sync.isoformat() if w.last_sync else None,
        "total_backups": w.total_backups,
        "total_size_mb": w.total_size_mb,
        "created_at": w.created_at.isoformat(),
        "updated_at": w.updated_at.isoformat()
    } for w in worlds]

@router.post("")
@limiter.limit("100/minute")
async def create_world(
    request: Request,
    world_data: WorldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new world entry.

    Registers a new Minecraft world in the system. The world must have a unique
    name for the current user. Optionally, a local path can be provided for
    tracking the world files.
    """
    
    # Check if world with same name exists
    existing = db.query(World).filter(
        World.user_id == current_user.id,
        World.name == world_data.name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="World with this name already exists")
    
    world = World(
        user_id=current_user.id,
        name=world_data.name,
        description=world_data.description,
        local_path=world_data.local_path
    )
    
    db.add(world)
    db.commit()
    db.refresh(world)
    
    return {
        "id": world.id,
        "name": world.name,
        "description": world.description,
        "created_at": world.created_at.isoformat()
    }

@router.get("/{world_id}")
@limiter.limit("100/minute")
async def get_world(
    request: Request,
    world_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details for a specific world.

    Returns comprehensive information about the world including sync settings,
    backup statistics, and timestamps. Only accessible to the world owner.
    """
    world = db.query(World).filter(
        World.id == world_id,
        World.user_id == current_user.id
    ).first()
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    return {
        "id": world.id,
        "name": world.name,
        "description": world.description,
        "local_path": world.local_path,
        "auto_sync_enabled": world.auto_sync_enabled,
        "sync_interval_minutes": world.sync_interval_minutes,
        "last_sync": world.last_sync.isoformat() if world.last_sync else None,
        "total_backups": world.total_backups,
        "total_size_mb": world.total_size_mb,
        "created_at": world.created_at.isoformat(),
        "updated_at": world.updated_at.isoformat()
    }

@router.put("/{world_id}")
@limiter.limit("100/minute")
async def update_world(
    request: Request,
    world_id: int,
    world_data: WorldUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update world settings and configuration.

    Allows partial updates to world properties. Only provided fields will be
    updated. Only accessible to the world owner.
    """
    world = db.query(World).filter(
        World.id == world_id,
        World.user_id == current_user.id
    ).first()
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    if world_data.name is not None:
        world.name = world_data.name
    if world_data.description is not None:
        world.description = world_data.description
    if world_data.local_path is not None:
        world.local_path = world_data.local_path
    if world_data.auto_sync_enabled is not None:
        world.auto_sync_enabled = world_data.auto_sync_enabled
    if world_data.sync_interval_minutes is not None:
        world.sync_interval_minutes = world_data.sync_interval_minutes
    
    db.commit()
    db.refresh(world)
    
    return {"message": "World updated successfully"}

@router.delete("/{world_id}")
@limiter.limit("100/minute")
async def delete_world(
    request: Request,
    world_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a world from the system.

    Removes the world record from the database. Note: Associated backups stored
    in Google Drive are NOT automatically deleted and must be removed manually
    if desired. Only accessible to the world owner.
    """
    world = db.query(World).filter(
        World.id == world_id,
        World.user_id == current_user.id
    ).first()
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    db.delete(world)
    db.commit()
    
    return {"message": "World deleted successfully"}