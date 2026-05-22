# Desktop App — Minecraft Backup

A self-contained desktop application that backs up Minecraft worlds to Google Drive. Runs entirely on the user's machine — no deployment, no separate servers.

## Stack

- **Backend:** FastAPI (Python 3.10+) with SQLAlchemy 2.0 + SQLite
- **Frontend:** Vanilla JS SPA with Tailwind CSS (CDN)
- **Auth:** Google OAuth 2.0 (PKCE) + JWT tokens
- **Storage:** Google Drive API v3
- **File Watcher:** watchdog (in-process background thread)
- **Encryption:** Fernet (from `cryptography`)

## Directory Structure

```
Exe/desktop-app/
├── main.py                 # Entry point — starts server + watcher
├── requirements.txt        # Python dependencies
├── .env                    # Environment config (Google OAuth keys)
├── .env.example            # Template for .env
├── app/
│   ├── __init__.py
│   ├── config.py           # Pydantic settings (reads from .env)
│   ├── database.py         # SQLAlchemy engine + session
│   ├── models.py           # ORM: User, World, Backup, PairingCode
│   ├── dependencies.py     # Auth dependency (JWT + API key)
│   ├── encryption.py       # Fernet encrypt/decrypt for credentials
│   ├── server.py           # FastAPI app creation, static file serving
│   ├── routers/
│   │   ├── auth.py         # Google OAuth, JWT, API keys, preferences
│   │   ├── worlds.py       # World CRUD
│   │   └── drive.py        # Backup upload/download/list/delete
│   └── services/
│       └── google_drive_service.py  # Google Drive API wrapper
├── static/
│   ├── index.html          # SPA shell
│   ├── app.js              # Frontend logic (all views + API client)
│   └── style.css           # Custom styles (dark theme)
└── watcher/
    ├── __init__.py
    └── watcher.py          # File system watcher (BackgroundWatcher)
```

## Setup

### Prerequisites
- Python 3.10+
- A Google Cloud project with the Drive API enabled
- A configured OAuth 2.0 consent screen

### Google Cloud Console Setup
1. Go to APIs & Services → Credentials → Create OAuth 2.0 Client ID
2. Set application type to **Web application**
3. Add this redirect URI:
   ```
   http://localhost:8710/api/auth/google/callback
   ```
4. Copy the Client ID and Client Secret

### Installation
```bash
cd Exe/desktop-app
cp .env.example .env
# Fill in your Google OAuth credentials in .env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

The app opens at `http://localhost:8710` automatically.

### Environment Variables (`.env`)
| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Used for JWT signing + Fernet encryption |
| `GOOGLE_CLIENT_ID` | Yes | — | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | — | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | No | `http://localhost:8710/api/auth/google/callback` | OAuth callback URL |
| `DATABASE_URL` | No | `sqlite:///./minecraft_backup.db` | SQLite database path |
| `DEBUG` | No | `false` | Enable debug mode |
| `MAX_UPLOAD_SIZE_MB` | No | `5120` | Max backup file size |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `10080` (7 days) | JWT token expiry |

## API Endpoints

All endpoints are prefixed with `/api`.

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/auth/login` | No | Returns Google OAuth URL |
| `GET` | `/auth/google/callback` | No | OAuth callback (code exchange) |
| `GET` | `/auth/me` | JWT | Current user profile |
| `PATCH` | `/auth/preferences` | JWT | Update auto-cleanup, max backups |
| `POST` | `/auth/logout` | JWT | Logout |
| `POST` | `/auth/refresh` | No | Exchange refresh token for new JWT |

### Worlds

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/worlds` | JWT | List all worlds |
| `POST` | `/worlds` | JWT | Create a world |
| `GET` | `/worlds/{id}` | JWT | Get world details |
| `PUT` | `/worlds/{id}` | JWT | Update world |
| `DELETE` | `/worlds/{id}` | JWT | Delete world |

### Drive / Backups

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/drive/worlds/{id}/backup` | JWT | Upload backup (multipart ZIP) |
| `GET` | `/drive/worlds/{id}/backups` | JWT | List backups for a world |
| `GET` | `/drive/worlds/{id}/backups/{bid}/download-link` | JWT | Get Drive download link |
| `DELETE` | `/drive/worlds/{id}/backups/{bid}` | JWT | Delete a backup |
| `GET` | `/drive/storage` | JWT | Google Drive storage quota |

### Health

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | No | Server health check |

## Authentication Flow

1. Frontend calls `GET /api/auth/login` → receives a Google OAuth URL
2. User is redirected to Google in their browser
3. After consent, Google redirects to `http://localhost:8710/api/auth/google/callback`
4. Backend exchanges the code for tokens, creates/updates the user in SQLite, encrypts and stores the Google credentials
5. Backend redirects the browser to `/?token=JWT&refresh_token=xxx`
6. Frontend saves the JWT in `localStorage`, clears the URL params, and shows the dashboard
7. Subsequent API calls include `Authorization: Bearer <token>`
8. On 401, the frontend attempts a token refresh via `/api/auth/refresh`

## Database Models

### User
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `email` | String | Unique, from Google |
| `google_id` | String | Unique, from Google |
| `display_name` | String | From Google profile |
| `profile_picture` | String | From Google profile |
| `google_credentials` | Text | Encrypted OAuth tokens |
| `drive_folder_id` | String | Google Drive "MinecraftBackups" folder ID |
| `auto_cleanup_enabled` | Boolean | Default: true |
| `max_backups_per_world` | Integer | Default: 10 |
| `refresh_token` | Text | Encrypted refresh token for JWT renewal |

### World
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `user_id` | Integer | FK → users.id |
| `name` | String | Unique per user |
| `description` | Text | Optional |
| `local_path` | String | Filesystem path for auto-watch |
| `drive_folder_id` | String | Google Drive folder for this world |
| `auto_sync_enabled` | Boolean | Toggle file watching |
| `sync_interval_minutes` | Integer | How often to sync worlds list |
| `total_backups` | Integer | Counter |
| `total_size_mb` | Float | Sum of backup sizes |

### Backup
| Column | Type | Notes |
|---|---|---|
| `id` | Integer | PK |
| `world_id` | Integer | FK → worlds.id |
| `drive_file_id` | String | Google Drive file ID (unique) |
| `filename` | String | Display name |
| `size_mb` | Float | File size |
| `backup_type` | String | "manual" or "auto" |
| `status` | String | "completed" or "failed" |

## Frontend Pages

All pages are rendered client-side by `app.js` within a single HTML shell.

| Page | Route State | Description |
|---|---|---|
| **Login** | `state.page === "login"` | Google sign-in button, centered card |
| **Dashboard** | `"dashboard"` | World cards grid, search, Drive storage widget, Add World button |
| **Add World** | `"add-world"` | Form: name, description, local path |
| **World Details** | `"world-details"` | World info, auto-sync toggle, upload backup, backup history table |
| **Settings** | `"settings"` | Account info, preferences, API key management, logout |

## File Watcher

The `BackupWatcher` runs in a background thread inside the main process. It:

1. Polls the database every 5 minutes for worlds with `auto_sync_enabled = true`
2. Starts a `watchdog` observer on each world's `local_path` (or `~/.minecraft/saves/<world_name>`)
3. On file changes, debounces for 10 seconds
4. Creates a ZIP of the world folder
5. Uploads to Google Drive using the world owner's credentials
6. Records a new `Backup` row (type: "auto")

The watcher is started/stopped automatically with the server via `main.py`.

## Known Issues & Notes

### Backup count goes negative
**Fixed.** The `total_backups` field was not being incremented when a backup was created. The delete endpoint subtracts from it, causing it to go negative. Fix: Added `world.total_backups += 1` in the upload handler.

### Watcher not wired in
**Fixed.** The watcher module existed but was not started by `main.py`. Fix: Integrated `BackupWatcher` into `main.py` with a database-backed world sync function and a backup callback that creates ZIPs and uploads to Drive.

### OAuth state stored in memory
Pending auth states are kept in a Python dict (`pending_auth_states`). This is lost on server restart. Acceptable for a local desktop app — the user just re-authenticates.

### OAuth crash fix (2026-05-22)
**Fixed.** The `beforeunload` handler in `app.js` called `POST /api/shutdown-now` when the browser navigated to Google's OAuth page, killing the server instantly. Fix: removed `beforeunload` handler, made heartbeat monitor OAuth-aware (defers shutdown while `pending_auth_states` is non-empty, extends heartbeat timeout to 300s).

### Token refresh requires scanning all users
The `/api/auth/refresh` endpoint iterates all users with refresh tokens to find a match. Fine for single-user/small-scale desktop use.

### No TypeScript or tests
Vanilla JS throughout. No automated tests. The app is minimal by design.

### Potential improvements
- Package with PyInstaller into a single executable
- Add a system tray icon (requires PyQt or similar)
- Replace vanilla JS frontend with the React app (built to static files)
- Add restore functionality (download + extract backup to save folder)
- Add backup retention settings UI (currently only auto-cleanup toggle)

## Configuration Reference

Full settings (`app/config.py`):

```python
APP_NAME: str = "Minecraft Backup"
SECRET_KEY: str = "change-me-to-something-secret"
DEBUG: bool = False
DATABASE_URL: str = "sqlite:///./minecraft_backup.db"
GOOGLE_CLIENT_ID: str = ""
GOOGLE_CLIENT_SECRET: str = ""
GOOGLE_REDIRECT_URI: str = "http://localhost:8710/api/auth/google/callback"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days
MAX_UPLOAD_SIZE_MB: int = 5120  # 5 GB
TEMP_UPLOAD_DIR: str = "/tmp/minecraft_uploads"
MAX_BACKUPS_PER_WORLD: int = 10
AUTO_CLEANUP_ENABLED: bool = True
```
