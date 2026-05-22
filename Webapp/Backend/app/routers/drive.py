from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
import json
from datetime import datetime
import tempfile
import shutil
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from app.database import get_db
from app.models.user import User, World, Backup
from app.dependencies import get_current_user
from app.services.google_drive_service import GoogleDriveService
from app.utils.encryption import decrypt_credentials
from app.config import get_settings

router = APIRouter(prefix="/api/drive", tags=["drive"])
settings = get_settings()
limiter = Limiter(key_func=get_remote_address)

# Thread pool for blocking I/O operations
executor = ThreadPoolExecutor(max_workers=4)

def get_drive_service(current_user: User) -> GoogleDriveService:
    """
    Initialize and return a Google Drive service for the authenticated user.

    Decrypts the user's stored OAuth credentials and creates a Drive service
    instance configured with their access tokens.

    Args:
        current_user: The authenticated user object with stored credentials.

    Returns:
        GoogleDriveService instance configured for the user's Drive.
    """
    credentials_json = decrypt_credentials(current_user.google_credentials)
    credentials_dict = json.loads(credentials_json)
    return GoogleDriveService(credentials_dict)

@router.post("/worlds/{world_id}/backup")
@limiter.limit("20/minute")
async def backup_world(
    request: Request,
    world_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and backup a Minecraft world to Google Drive.

    Accepts a ZIP file containing the Minecraft world data, uploads it to
    the user's Google Drive in the appropriate world folder, and creates
    a backup record in the database. Automatically deletes the previous
    backup to prevent storage from filling up with old versions.
    """
    
    # Get world
    world = db.query(World).filter(
        World.id == world_id,
        World.user_id == current_user.id
    ).first()
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    # Validate file
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Only ZIP files are accepted")
    
    # Check file size
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB} MB"
        )
    
    # Save uploaded file temporarily
    temp_dir = Path(settings.TEMP_UPLOAD_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    temp_file_path = temp_dir / f"{world_id}_{datetime.now().timestamp()}.zip"
    
    try:
        # Save uploaded file to temp using blocking I/O in executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor,
            partial(_save_uploaded_file, file, temp_file_path)
        )
        
        # Initialize Drive service
        drive_service = get_drive_service(current_user)
        
        # Create world folder in Drive if doesn't exist
        if not world.drive_folder_id:
            # This is a fast API call, can run in executor too if needed
            world.drive_folder_id = drive_service.create_world_folder(
                world_name=world.name,
                parent_folder_id=current_user.drive_folder_id
            )
            db.commit()
        
        # Delete the previous backup if exists (to keep only 1 latest backup)
        # This prevents Google Drive from filling up with old versions
        latest_backup = db.query(Backup).filter(
            Backup.world_id == world.id,
            Backup.status == 'completed'
        ).order_by(Backup.created_at.desc()).first()
        
        if latest_backup:
            print(f"🗑️ Deleting old backup: {latest_backup.filename} (ID: {latest_backup.id})")
            try:
                # Delete from Google Drive
                drive_service.delete_backup(latest_backup.drive_file_id)
                # Delete from database
                db.delete(latest_backup)
                db.commit()
                print(f"✅ Old backup deleted successfully")
            except Exception as e:
                print(f"⚠️ Failed to delete old backup: {e}")
                db.rollback()
        
        # Upload to Drive - this is blocking and can take a long time
        # Run in executor to avoid blocking the event loop
        upload_result = await loop.run_in_executor(
            executor,
            partial(drive_service.upload_world_backup,
                world_path=temp_file_path,
                world_name=world.name,
                folder_id=world.drive_folder_id
            )
        )
        
        backup_info = upload_result
        
        # Save backup record
        backup = Backup(
            world_id=world.id,
            drive_file_id=backup_info['file_id'],
            filename=backup_info['name'],
            size_mb=backup_info['size_mb'],
            backup_type='manual',
            status='completed'
        )
        db.add(backup)
        
        # Update world statistics (replacing old backup, so count stays the same)
        world.last_sync = datetime.utcnow()
        world.total_size_mb = backup_info['size_mb']
        
        db.commit()
        db.refresh(backup)
        
        # Cleanup old backups in background
        if background_tasks and current_user.auto_cleanup_enabled:
            background_tasks.add_task(
                drive_service.cleanup_old_backups,
                folder_id=world.drive_folder_id,
                keep_count=current_user.max_backups_per_world
            )
        
        return {
            "success": True,
            "message": "Backup created successfully",
            "backup": {
                "id": backup.id,
                "filename": backup.filename,
                "size_mb": backup.size_mb,
                "created_at": backup.created_at.isoformat(),
                "web_link": backup_info.get('web_link')
            }
        }
        
    except Exception as e:
        # If backup failed, mark it in database
        if 'backup' in locals():
            backup.status = 'failed'
            backup.error_message = str(e)
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path.exists():
            temp_file_path.unlink()

def _save_uploaded_file(file: UploadFile, temp_path: Path):
    """
    Save uploaded file to disk (blocking I/O operation).

    Helper function executed in a thread pool to prevent blocking the
    FastAPI event loop during file write operations.

    Args:
        file: FastAPI UploadFile object.
        temp_path: Destination path for the temporary file.
    """
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

@router.get("/worlds/{world_id}/backups")
@limiter.limit("100/minute")
async def list_backups(
    request: Request,
    world_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all backups for a world"""
    
    world = db.query(World).filter(
        World.id == world_id,
        World.user_id == current_user.id
    ).first()
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    backups = db.query(Backup).filter(
        Backup.world_id == world_id
    ).order_by(Backup.created_at.desc()).all()
    
    return {
        "world_name": world.name,
        "total_backups": len(backups),
        "total_size_mb": sum(b.size_mb for b in backups),
        "backups": [{
            "id": b.id,
            "filename": b.filename,
            "size_mb": b.size_mb,
            "backup_type": b.backup_type,
            "status": b.status,
            "created_at": b.created_at.isoformat(),
            "drive_file_id": b.drive_file_id
        } for b in backups]
    }

@router.get("/worlds/{world_id}/backups/{backup_id}/download-link")
@limiter.limit("100/minute")
async def get_download_link(
    request: Request,
    world_id: int,
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get direct download link for a backup"""
    
    world = db.query(World).filter(
        World.id == world_id,
        World.user_id == current_user.id
    ).first()
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    backup = db.query(Backup).filter(
        Backup.id == backup_id,
        Backup.world_id == world_id
    ).first()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    drive_service = get_drive_service(current_user)
    
    # Get file info with download link
    file_info = drive_service.service.files().get(
        fileId=backup.drive_file_id,
        fields='webContentLink, webViewLink'
    ).execute()
    
    return {
        "download_link": file_info.get('webContentLink'),
        "view_link": file_info.get('webViewLink'),
        "filename": backup.filename
    }

@router.delete("/worlds/{world_id}/backups/{backup_id}")
@limiter.limit("100/minute")
async def delete_backup(
    request: Request,
    world_id: int,
    backup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific backup"""
    
    world = db.query(World).filter(
        World.id == world_id,
        World.user_id == current_user.id
    ).first()
    
    if not world:
        raise HTTPException(status_code=404, detail="World not found")
    
    backup = db.query(Backup).filter(
        Backup.id == backup_id,
        Backup.world_id == world_id
    ).first()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    drive_service = get_drive_service(current_user)
    
    try:
        # Delete from Drive
        drive_service.delete_backup(backup.drive_file_id)
        
        # Update world statistics
        world.total_backups -= 1
        world.total_size_mb -= backup.size_mb
        
        # Delete from database
        db.delete(backup)
        db.commit()
        
        return {"message": "Backup deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")

@router.get("/storage")
@limiter.limit("100/minute")
async def get_storage_info(request: Request, current_user: User = Depends(get_current_user)):
    """Get user's Google Drive storage information"""
    
    drive_service = get_drive_service(current_user)
    quota = drive_service.get_storage_quota()
    
    return quota