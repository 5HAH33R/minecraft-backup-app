#!/usr/bin/env python3
"""Minecraft Backup Desktop App"""
import sys
import os

# Add parent dir to path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.server import create_app, mount_static
from app.config import get_settings

# ─── Logging setup ──────────────────────────────────────────
# Must happen after config loads (which resolves DATA_DIR).
_settings = get_settings()
_log_dir = _settings.DATA_DIR
_log_dir.mkdir(parents=True, exist_ok=True)
_log_path = _log_dir / "app.log"

import logging

handlers = [logging.FileHandler(str(_log_path), encoding="utf-8")]
if sys.stdout is not None:
    handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=handlers,
)
logger = logging.getLogger("minecraft-backup")

# PyInstaller console=False leaves sys.stdout/stderr as None,
# which crashes uvicorn's logging config on startup.
# Redirect to the log file so all output is captured.
if sys.stdout is None:
    sys.stdout = open(str(_log_path), "a", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(str(_log_path), "a", encoding="utf-8")

import uvicorn
import webbrowser
import threading
import time
import signal
import json
from pathlib import Path
from datetime import datetime, UTC
import zipfile

from app.database import SessionLocal
from app.models import User, World, Backup
from app.encryption import decrypt_credentials
from app.services.google_drive_service import GoogleDriveService
from watcher.watcher import BackupWatcher
from app.watcher_events import check_and_consume_resync
from app.watcher_status import set_status
from app.routers.auth import pending_auth_states

PORT = 8710
HOST = "127.0.0.1"
app = create_app()

_watcher = None

# ─── Single-instance check ─────────────────────────────
import socket
import urllib.request

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((HOST, PORT))
sock.close()
if result == 0:
    # Already running — use subprocess to reliably open browser (webbrowser module is unreliable on Windows)
    import subprocess
    try:
        subprocess.Popen(f'start "" "http://{HOST}:{PORT}"', shell=True)
    except Exception:
        pass
    try:
        urllib.request.urlopen(f"http://{HOST}:{PORT}/api/reload", timeout=5)
    except Exception:
        pass
    print("App is already running. Opening browser tab.")
    sys.exit(0)

# ─── Heartbeat + shutdown ────────────────────────────
# Frontend sends a heartbeat every 3s while the tab is open.
# Tab close → sendBeacon("/api/shutdown") → 120s countdown starts.
# OAuth redirect → countdown starts again → new page heartbeat cancels it.
# Fallback: no heartbeat for 25s kills process (or 300s during OAuth flow).
_last_heartbeat = None
_shutdown_at = None
_shutdown_pending = False
HEARTBEAT_TIMEOUT = 25
SHUTDOWN_DELAY = 120
OAUTH_TIMEOUT = 300


@app.post("/api/heartbeat")
async def heartbeat():
    global _last_heartbeat, _shutdown_at, _shutdown_pending
    _last_heartbeat = time.time()
    _shutdown_at = None  # Cancel tab-close countdown (e.g. OAuth return)
    _shutdown_pending = False  # Cancel explicit shutdown request
    return {"ok": True}


@app.post("/api/shutdown")
async def shutdown():
    """Start shutdown countdown — called via sendBeacon on tab close.
    Heartbeat cancels this, so OAuth redirect (page reload → heartbeat) works."""
    global _shutdown_at
    if _shutdown_at is None:
        _shutdown_at = time.time() + SHUTDOWN_DELAY
        logger.info(f"Shutdown requested — will shut down in {SHUTDOWN_DELAY}s unless cancelled")
    return {"ok": True}


@app.post("/api/shutdown-now")
async def shutdown_now():
    """Immediate shutdown — called from UI Shut Down button."""
    global _shutdown_pending
    logger.info("Immediate shutdown requested")
    _shutdown_pending = True  # Monitor loop will pick this up
    return {"ok": True}


@app.get("/api/reload")
async def reload_browser():
    """Open/reload the browser tab — called when exe is clicked again."""
    import subprocess
    try:
        subprocess.Popen(f'start "" "http://{HOST}:{PORT}"', shell=True)
    except Exception:
        pass
    return {"ok": True}


# Mount static files AFTER all API routes so routes take priority over the catch-all
mount_static(app)


def _heartbeat_monitor():
    global _last_heartbeat, _shutdown_at, _shutdown_pending
    while True:
        time.sleep(2)
        # Explicit shutdown request (Shut Down App button)
        if _shutdown_pending and not pending_auth_states:
            logger.info("Shut Down button pressed — shutting down")
            os._exit(0)
        # Tab-close countdown expired (beforeunload → /api/shutdown)
        if _shutdown_at is not None and time.time() > _shutdown_at and not pending_auth_states:
            logger.info("Shutdown timer expired")
            os._exit(0)
        # Fallback: no heartbeat for too long
        if _last_heartbeat is not None:
            elapsed = time.time() - _last_heartbeat
            # When OAuth is in progress, use a much longer timeout so the
            # server doesn't kill itself while the user is on Google's auth page.
            timeout = OAUTH_TIMEOUT if pending_auth_states else HEARTBEAT_TIMEOUT
            if elapsed > timeout:
                logger.info("No heartbeat for too long — shutting down")
                os._exit(0)


def open_browser():
    time.sleep(1.5)
    import subprocess
    try:
        subprocess.Popen(f'start "" "http://{HOST}:{PORT}"', shell=True)
    except Exception:
        pass


def _watcher_backup(world_dict, world_path, done_callback=None):
    """Backup function called by the watcher when file changes are detected."""
    db = SessionLocal()
    world_id = world_dict["id"]
    world_name = world_dict.get("name", "Unknown")
    try:
        world = db.query(World).filter(World.id == world_id).first()
        if not world:
            return

        user = db.query(User).filter(User.id == world.user_id).first()
        if not user or not user.google_credentials:
            return

        creds = json.loads(decrypt_credentials(user.google_credentials))
        drive = GoogleDriveService(creds)

        if not world.drive_folder_id:
            world.drive_folder_id = drive.create_world_folder(
                world_name=world.name,
                parent_folder_id=user.drive_folder_id,
            )
            db.commit()

        # Persistent zip path — survives temp dir cleanup, deleted after upload
        zip_dir = _settings.DATA_DIR / "uploads"
        zip_dir.mkdir(parents=True, exist_ok=True)
        zip_path = zip_dir / f"world_{world_id}_backup.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in Path(world_path).rglob("*"):
                if fp.is_file():
                    compress = zipfile.ZIP_STORED if fp.suffix.lower() == ".mca" else zipfile.ZIP_DEFLATED
                    try:
                        zf.write(fp, fp.relative_to(Path(world_path).parent), compress_type=compress)
                    except (PermissionError, OSError):
                        pass

        result = drive.upload_world_backup(
            world_path=str(zip_path),
            world_name=world.name,
            folder_id=world.drive_folder_id,
        )

        backup = Backup(
            world_id=world.id,
            drive_file_id=result["file_id"],
            filename=result["name"],
            size_mb=result["size_mb"],
            backup_type="auto",
            status="completed",
        )
        db.add(backup)
        world.total_backups += 1
        world.last_sync = datetime.now(UTC)
        world.total_size_mb = (world.total_size_mb or 0) + result["size_mb"]
        db.commit()

        # Cleanup old backups per user preference
        if user.auto_cleanup_enabled and user.max_backups_per_world > 0:
            all_backups = (
                db.query(Backup)
                .filter(Backup.world_id == world.id, Backup.status == "completed")
                .order_by(Backup.created_at.desc())
                .all()
            )
            if len(all_backups) > user.max_backups_per_world:
                for b in all_backups[user.max_backups_per_world:]:
                    try:
                        drive.delete_backup(b.drive_file_id)
                    except Exception:
                        pass
                    db.delete(b)
                db.commit()

        set_status(world.id, world.name, "completed", "Backup complete!")
        # Reset status to idle after 30s
        threading.Timer(30, lambda: set_status(world.id, world.name, "idle", "Watching for changes")).start()
        logger.info(f"Auto-backup complete: {world.name}")

    except Exception as e:
        set_status(world_id, world_name, "error", f"Backup failed: {e}")
        logger.error(f"Auto-backup failed for {world_name}: {e}")
        db.rollback()
    finally:
        db.close()
        done_callback and done_callback(world_id)
        if "zip_path" in locals() and zip_path.exists():
            try:
                zip_path.unlink()
            except Exception:
                pass


def start_watcher():
    global _watcher

    def get_worlds():
        db = SessionLocal()
        try:
            worlds = db.query(World).filter(World.auto_sync_enabled == True).all()
            return [
                {
                    "id": w.id,
                    "name": w.name,
                    "local_path": w.local_path,
                    "auto_sync_enabled": w.auto_sync_enabled,
                    "user_id": w.user_id,
                }
                for w in worlds
            ]
        finally:
            db.close()

    _watcher = BackupWatcher(
        get_worlds_fn=get_worlds,
        backup_fn=_watcher_backup,
        debounce_seconds=10,
        sync_interval=300,
        resync_check_fn=check_and_consume_resync,
    )
    _watcher.start()


def stop_watcher():
    global _watcher
    if _watcher:
        _watcher.stop()


def signal_handler(sig, frame):
    logger.info("Shutting down...")
    stop_watcher()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print(f"  Minecraft Backup Desktop App")
    print(f"  ─────────────────────────────")
    print(f"  Open: http://{HOST}:{PORT}")
    print(f"  Press Ctrl+C to stop")
    print()

    start_watcher()
    threading.Thread(target=open_browser, daemon=True).start()
    threading.Thread(target=_heartbeat_monitor, daemon=True).start()

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )
