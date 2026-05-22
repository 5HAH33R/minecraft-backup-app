from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import os

from app.config import get_settings
from app.database import engine, Base
from app.routers import auth, worlds, drive, watcher, status

# Resolve static dir — works in dev and PyInstaller bundles
_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))
STATIC_DIR = str(_ROOT / "static")


def create_app():
    settings = get_settings()

    # Ensure persistent data directory exists
    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)

    app = FastAPI(title="Minecraft Backup Desktop", version="1.0.0")

    app.include_router(auth.router, prefix="/api")
    app.include_router(worlds.router, prefix="/api")
    app.include_router(drive.router, prefix="/api")
    app.include_router(watcher.router, prefix="/api")
    app.include_router(status.router, prefix="/api")

    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "app": "Minecraft Backup Desktop"}

    return app


def mount_static(app):
    """Mount static files at / — call AFTER all API routes are registered so routes take priority."""
    if os.path.isdir(STATIC_DIR):
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
