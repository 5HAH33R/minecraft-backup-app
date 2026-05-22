from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List
from pathlib import Path
import sys
import secrets
import os


# ─── Embedded credentials ──────────────────────────────────────
# Replace these with YOUR Google Cloud OAuth credentials.
# Users authenticate via these — no per-user Google Cloud setup needed.
_EMBEDDED_GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
_EMBEDDED_GOOGLE_CLIENT_SECRET = "your-client-secret"


def _app_root() -> Path:
    """Root for bundled static assets — resolved from _MEIPASS in PyInstaller, or dev tree."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent))


def _data_dir() -> Path:
    """Persistent data directory, always alongside the executable. Fully portable.

    In PyInstaller bundles _MEIPASS is a temp dir, so we use sys.executable instead.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys.executable).parent / "data"
    return Path(__file__).parent.parent / "data"


def _ensure_secret_key(key_file: Path) -> str:
    """Read SECRET_KEY from file, or generate and persist one."""
    if key_file.exists():
        return key_file.read_text().strip()
    key = secrets.token_urlsafe(48)
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text(key)
    return key


class Settings(BaseSettings):
    APP_NAME: str = "Minecraft Backup"
    SECRET_KEY: str = ""
    DEBUG: bool = False

    GOOGLE_CLIENT_ID: str = _EMBEDDED_GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET: str = _EMBEDDED_GOOGLE_CLIENT_SECRET
    GOOGLE_REDIRECT_URI: str = "http://localhost:8710/api/auth/google/callback"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = ""
    TEMP_UPLOAD_DIR: str = ""
    MAX_UPLOAD_SIZE_MB: int = 5120
    MAX_BACKUPS_PER_WORLD: int = 10
    AUTO_CLEANUP_ENABLED: bool = True

    GOOGLE_SCOPES: List[str] = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/drive.file",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    def __init__(self, **kwargs):
        # Allow overriding embedded credentials via env vars for development
        env_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        env_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")

        super().__init__(**kwargs)

        # Env vars take priority over embedded values
        if env_client_id:
            self.GOOGLE_CLIENT_ID = env_client_id
        if env_client_secret:
            self.GOOGLE_CLIENT_SECRET = env_client_secret

        # Resolve paths relative to app root
        self._root = _app_root()
        self._data = _data_dir()

        # Persist SECRET_KEY to data directory
        key_file = self._data / "secret.key"
        self.SECRET_KEY = _ensure_secret_key(key_file)

        # Build derived paths
        self.DATABASE_URL = f"sqlite:///{self._data / 'minecraft_backup.db'}"
        self.TEMP_UPLOAD_DIR = str(self._data / "uploads")

    @property
    def APP_ROOT(self) -> Path:
        return self._root

    @property
    def DATA_DIR(self) -> Path:
        return self._data

    @property
    def google_scopes_string(self) -> str:
        return "%20".join(self.GOOGLE_SCOPES)


@lru_cache()
def get_settings():
    return Settings()
