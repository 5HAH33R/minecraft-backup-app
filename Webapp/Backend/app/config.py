from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "Minecraft Backup"
    SECRET_KEY: str
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "sqlite:///./minecraft_backup.db"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 5120
    TEMP_UPLOAD_DIR: str = "/tmp/minecraft_uploads"
    
    # Backup Settings
    MAX_BACKUPS_PER_WORLD: int = 10
    AUTO_CLEANUP_ENABLED: bool = True

    # Google OAuth Scopes
    GOOGLE_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/drive.file"
    ]

    @property
    def google_scopes_string(self) -> str:
        """Returns space-separated scopes for OAuth URL"""
        return "%20".join(self.GOOGLE_SCOPES)

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()