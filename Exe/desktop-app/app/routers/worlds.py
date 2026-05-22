from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import User, World
from app.dependencies import get_current_user

router = APIRouter(tags=["worlds"])


class WorldCreate(BaseModel):
    name: str
    description: Optional[str] = None
    local_path: Optional[str] = None


class WorldUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    local_path: Optional[str] = None
    auto_sync_enabled: Optional[bool] = None
    sync_interval_minutes: Optional[int] = None


@router.get("/worlds")
async def list_worlds(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    worlds = db.query(World).filter(World.user_id == current_user.id).all()
    return [
        {
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
            "updated_at": w.updated_at.isoformat(),
        }
        for w in worlds
    ]


@router.post("/worlds")
async def create_world(
    world_data: WorldCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(World)
        .filter(World.user_id == current_user.id, World.name == world_data.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="World with this name already exists")

    world = World(
        user_id=current_user.id,
        name=world_data.name,
        description=world_data.description,
        local_path=world_data.local_path,
    )
    db.add(world)
    db.commit()
    db.refresh(world)

    return {
        "id": world.id,
        "name": world.name,
        "description": world.description,
        "created_at": world.created_at.isoformat(),
    }


@router.get("/worlds/{world_id}")
async def get_world(
    world_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    world = (
        db.query(World)
        .filter(World.id == world_id, World.user_id == current_user.id)
        .first()
    )
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
        "updated_at": world.updated_at.isoformat(),
    }


@router.put("/worlds/{world_id}")
async def update_world(
    world_id: int,
    world_data: WorldUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    world = (
        db.query(World)
        .filter(World.id == world_id, World.user_id == current_user.id)
        .first()
    )
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
    return {"message": "World updated successfully"}


@router.delete("/worlds/{world_id}")
async def delete_world(
    world_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    world = (
        db.query(World)
        .filter(World.id == world_id, World.user_id == current_user.id)
        .first()
    )
    if not world:
        raise HTTPException(status_code=404, detail="World not found")

    db.delete(world)
    db.commit()
    return {"message": "World deleted successfully"}
