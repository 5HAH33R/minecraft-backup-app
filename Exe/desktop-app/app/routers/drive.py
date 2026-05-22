from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime, UTC
import json
import logging
import shutil
import zipfile
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from app.database import get_db
from app.models import User, World, Backup
from app.dependencies import get_current_user
from app.services.google_drive_service import GoogleDriveService
from app.encryption import decrypt_credentials
from app.config import get_settings

router = APIRouter(tags=["drive"])
settings = get_settings()
executor = ThreadPoolExecutor(max_workers=4)
logger = logging.getLogger("minecraft-backup.drive")


def _get_drive_service(user: User) -> GoogleDriveService:
    creds_json = decrypt_credentials(user.google_credentials)
    creds_dict = json.loads(creds_json)
    return GoogleDriveService(creds_dict)


def _save_upload(file: UploadFile, dest: Path):
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)


@router.post("/drive/worlds/{world_id}/backup")
async def backup_world(
    world_id: int,
    file: UploadFile = File(...),
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

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file.file.seek(0, 2)
    fsize = file.file.tell()
    file.file.seek(0)
    if fsize > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum is {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    temp_dir = Path(settings.TEMP_UPLOAD_DIR)
    temp_dir.mkdir(parents=True, exist_ok=True)
    original_name = file.filename
    temp_path = temp_dir / f"{world_id}_{datetime.now().timestamp()}_{original_name}"

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, partial(_save_upload, file, temp_path))

        # Wrap non-zip files in a zip before uploading
        if not original_name.lower().endswith(".zip"):
            zip_path = temp_path.with_suffix(".zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(temp_path, original_name)
            temp_path.unlink()
            temp_path = zip_path

        drive = _get_drive_service(current_user)

        if not world.drive_folder_id:
            world.drive_folder_id = drive.create_world_folder(
                world_name=world.name,
                parent_folder_id=current_user.drive_folder_id,
            )
            db.commit()

        # Upload new backup first
        result = await loop.run_in_executor(
            executor,
            partial(
                drive.upload_world_backup,
                world_path=str(temp_path),
                world_name=world.name,
                folder_id=world.drive_folder_id,
            ),
        )

        backup = Backup(
            world_id=world.id,
            drive_file_id=result["file_id"],
            filename=result["name"],
            size_mb=result["size_mb"],
            backup_type="manual",
            status="completed",
        )
        db.add(backup)

        world.total_backups += 1
        world.last_sync = datetime.now(UTC)
        world.total_size_mb = (world.total_size_mb or 0) + result["size_mb"]
        db.commit()
        db.refresh(backup)

        # Remove excess backups per user preference
        if current_user.auto_cleanup_enabled and current_user.max_backups_per_world > 0:
            all_backups = (
                db.query(Backup)
                .filter(Backup.world_id == world.id, Backup.status == "completed")
                .order_by(Backup.created_at.desc())
                .all()
            )
            if len(all_backups) > current_user.max_backups_per_world:
                for b in all_backups[current_user.max_backups_per_world:]:
                    try:
                        drive.delete_backup(b.drive_file_id)
                    except Exception as e:
                        logger.warning(f"Failed to delete Drive file {b.drive_file_id}: {e}")
                    db.delete(b)
                db.commit()

        return {
            "success": True,
            "message": "Backup created successfully",
            "backup": {
                "id": backup.id,
                "filename": backup.filename,
                "size_mb": backup.size_mb,
                "created_at": backup.created_at.isoformat(),
                "web_link": result.get("web_link"),
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.get("/drive/worlds/{world_id}/backups")
async def list_backups(
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

    backups = (
        db.query(Backup)
        .filter(Backup.world_id == world_id)
        .order_by(Backup.created_at.desc())
        .all()
    )

    return {
        "world_name": world.name,
        "total_backups": len(backups),
        "total_size_mb": sum(b.size_mb for b in backups),
        "backups": [
            {
                "id": b.id,
                "filename": b.filename,
                "size_mb": b.size_mb,
                "backup_type": b.backup_type,
                "status": b.status,
                "created_at": b.created_at.isoformat(),
                "drive_file_id": b.drive_file_id,
            }
            for b in backups
        ],
    }


@router.get("/drive/worlds/{world_id}/backups/{backup_id}/download-link")
async def get_download_link(
    world_id: int,
    backup_id: int,
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

    backup = (
        db.query(Backup)
        .filter(Backup.id == backup_id, Backup.world_id == world_id)
        .first()
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    drive = _get_drive_service(current_user)
    info = (
        drive.service.files()
        .get(fileId=backup.drive_file_id, fields="webContentLink, webViewLink")
        .execute()
    )

    return {
        "download_link": info.get("webContentLink"),
        "view_link": info.get("webViewLink"),
        "filename": backup.filename,
    }


@router.delete("/drive/worlds/{world_id}/backups/{backup_id}")
async def delete_backup(
    world_id: int,
    backup_id: int,
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

    backup = (
        db.query(Backup)
        .filter(Backup.id == backup_id, Backup.world_id == world_id)
        .first()
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")

    drive = _get_drive_service(current_user)
    try:
        drive.delete_backup(backup.drive_file_id)
        world.total_backups -= 1
        world.total_size_mb -= backup.size_mb
        db.delete(backup)
        db.commit()
        return {"message": "Backup deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")


@router.get("/drive/storage")
async def get_storage_info(current_user: User = Depends(get_current_user)):
    drive = _get_drive_service(current_user)
    return drive.get_storage_quota()
