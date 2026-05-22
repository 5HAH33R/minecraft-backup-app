from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.config import get_settings
from app.database import engine, Base, get_db
from app.routers import auth, worlds, drive, api_keys, refresh, pairing
import os
import logging
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

# Create temp upload directory
os.makedirs(settings.TEMP_UPLOAD_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    description="Backup your Minecraft worlds to Google Drive",
    version="1.0.0"
)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(worlds.router)
app.include_router(drive.router)
app.include_router(api_keys.router)
app.include_router(refresh.router)
app.include_router(pairing.router)

@app.get("/")
async def root():
    return {
        "message": "Minecraft Backup API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "healthy"}

@app.get("/health/live")
async def liveness():
    """Liveness probe - confirms the app is running"""
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness(db=Depends(get_db)):
    """Readiness probe - confirms the app can serve traffic"""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {"status": "not ready", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)