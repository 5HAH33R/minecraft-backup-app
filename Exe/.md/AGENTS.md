# Minecraft Backup App Agent Guide

Monorepo containing a FastAPI backend, React frontend, and a Python watchdog desktop agent for backing up Minecraft worlds to Google Drive.

---

## Project Structure

```
minecraft-backup-app/
├── Backend/                 # FastAPI backend (Python)
│   ├── app/
│   │   ├── main.py        # FastAPI app entry point
│   │   ├── config.py      # Pydantic settings configuration
│   │   ├── database.py   # SQLAlchemy database setup
│   │   ├── dependencies.py # FastAPI dependencies (auth)
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API endpoints
│   │   │   ├── auth.py   # Google OAuth login/logout
│   │   │   ├── worlds.py # World CRUD operations
│   │   │   └── drive.py  # Backup upload/download
│   │   ├── services/     # Business logic
│   │   │   └── google_drive_service.py # Google Drive API
│   │   └── utils/        # Utilities
│   │       └── encryption.py # Credentials encryption
│   ├── .env              # Environment variables
│   └── requirements.txt   # Python dependencies
├── frontend/              # React frontend
│   ├── src/
│   │   ├── pages/        # React pages
│   │   ├── components/   # Reusable components
│   │   ├── contexts/    # React contexts (Auth)
│   │   └── services/    # API services
│   ├── .env             # Frontend env (REACT_APP_API_URL)
│   └── package.json
├── desktop-agent/        # Python watchdog agent
│   ├── main.py          # Agent entry point
│   ├── config.json      # Agent configuration
│   └── requirements.txt
├── SESSION_SUMMARY.md    # Session documentation
├── PRODUCTION_READY.md  # Production deployment plan
└── CODE_OPTIMIZATION.md # Code refactoring guide
```

---

## Architecture Overview

### User Flow
1. User logs in via Google OAuth (frontend → backend → Google)
2. User adds a Minecraft world (specifies name, local path)
3. User can manually upload a backup ZIP file via frontend
4. OR User enables auto-sync, and the desktop agent monitors changes
5. When changes detected → agent compresses world → uploads to backend → backend pushes to Google Drive

### Key Components

| Component | Technology | Purpose |
|-----------|-------------|---------|
| Backend API | FastAPI (Python) | REST API for all operations |
| Frontend | React + Tailwind | Web UI |
| Database | SQLite | Local storage for users/worlds/backups |
| File Storage | Google Drive | Stores backup ZIP files |
| Desktop Agent | Python + watchdog | Monitors Minecraft save folders |

---

## Backend (FastAPI)

### Directory
`/Backend`

### Run Command
```bash
cd Backend
PYTHONPATH=. python -m app.main
```
Or simply:
```bash
python app/main.py
```
(From the Backend directory)

### Environment Variables (`.env`)
```
APP_NAME="Minecraft Backup"
SECRET_KEY=<generate-strong-secret>
DEBUG=True
DATABASE_URL=sqlite:///./minecraft_backup.db
GOOGLE_CLIENT_ID=<from-google-cloud-console>
GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
ACCESS_TOKEN_EXPIRE_MINUTES=10080
MAX_UPLOAD_SIZE_MB=5120
TEMP_UPLOAD_DIR=./temp_uploads
ALLOWED_ORIGINS=http://localhost:3000
```

### Database
- SQLite: `minecraft_backup.db` in Backend directory
- Schema: Auto-created via SQLAlchemy `Base.metadata.create_all()` in `app/main.py`
- **Do NOT use Alembic** - schema changes applied on startup

### API Endpoints

#### Auth (`/api/auth`)
- `GET /api/auth/google/login` - Start OAuth flow
- `GET /api/auth/google/callback` - OAuth callback
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

#### Worlds (`/api/worlds`)
- `GET /api/worlds` - List all worlds
- `POST /api/worlds` - Create world
- `GET /api/worlds/{id}` - Get world details
- `PUT /api/worlds/{id}` - Update world (name, description, local_path, auto_sync_enabled)
- `DELETE /api/worlds/{id}` - Delete world

#### Drive (`/api/drive`)
- `POST /api/drive/worlds/{id}/backup` - Upload backup ZIP
- `GET /api/drive/worlds/{id}/backups` - List backups
- `GET /api/drive/worlds/{id}/backups/{backup_id}/download-link` - Get download link
- `DELETE /api/drive/worlds/{id}/backups/{backup_id}` - Delete backup
- `GET /api/drive/storage` - Get Google Drive storage quota

### Important Details
- **Imports:** Use absolute imports (e.g., `from app.config import get_settings`)
- **CORS:** Must match frontend URL in `ALLOWED_ORIGINS`
- **Uploads:** `TEMP_UPLOAD_DIR` must exist and be writable

---

## Frontend (React)

### Directory
`/frontend`

### Run Command
```bash
cd frontend
npm install
npm start
```

### Environment Variables (`.env`)
```
REACT_APP_API_URL=http://localhost:8000
```

### Key Pages
- `/` - Login page
- `/dashboard` - List worlds, add new world
- `/add-world` - Create new world
- `/worlds/{id}` - World details, enable auto-sync, upload manual backup
- `/settings` - User settings

---

## Desktop Agent (Python)

### Directory
`/desktop-agent`

### Run Command
```bash
cd desktop-agent
python main.py
```

### Configuration (`config.json`)
Located in `desktop-agent/config.json`:
```json
{
  "api_url": "http://localhost:8000",
  "auth_token": "<jwt-token-from-frontend>",
  "minecraft_saves_path": "",
  "watched_worlds": [],
  "sync_interval_minutes": 30,
  "debounce_seconds": 10
}
```

### How It Works
1. **Sync:** Periodically fetches worlds from API (`/api/worlds`)
2. **Watch:** Uses `watchdog` to monitor folders for file changes
3. **Debounce:** Waits `debounce_seconds` after last change before backing up
4. **Compress:** Creates ZIP of world folder
5. **Upload:** Sends ZIP to backend (`POST /api/drive/worlds/{id}/backup`)
6. **Cleanup:** Backend deletes old backup before uploading new one

### Prerequisites
- Backend must be running
- Valid `auth_token` in `config.json` (get from frontend after login)
- World must have `local_path` set for auto-sync to work

---

## Key Quirks & Gotchas

1. **Backend Imports:** Always run with `PYTHONPATH=.` from Backend root to avoid `ModuleNotFoundError`
2. **Migrations:** Do NOT use `alembic upgrade` - schema changes applied on startup
3. **Uploads:** Ensure `TEMP_UPLOAD_DIR` (from backend `.env`) is a valid path
4. **CORS:** `ALLOWED_ORIGINS` in backend config must match frontend URL
5. **Agent Config:** Uses `./config.json` (in agent directory), NOT `~/.minecraft_backup/`
6. **Auto-Sync:** Requires `local_path` to be set on the world in the database
7. **Backup Deletion:** Backend automatically deletes the previous backup before uploading new one to save Google Drive space

---

## Authentication Flow

1. **Frontend** calls `GET /api/auth/google/login`
2. **Backend** returns OAuth URL with PKCE
3. **User** redirected to Google, logs in
4. **Google** redirects to `/api/auth/google/callback` with code
5. **Backend** exchanges code for tokens, creates user, creates app folder in Google Drive
6. **Backend** creates JWT, redirects to frontend with token
7. **Frontend** stores token in localStorage
8. **Desktop Agent** reads token from config.json

---

## Google Drive Structure

```
My Drive/
└── MinecraftBackups/           (Created on first login)
    └── {World Name}/           (Created per world)
        └── {world}_{timestamp}.zip  (Backups)
```

---

## Database Schema

### Users
- id, email, google_id, display_name, profile_picture
- google_credentials (encrypted), drive_folder_id
- auto_cleanup_enabled, max_backups_per_world

### Worlds
- id, user_id, name, description, local_path
- drive_folder_id, auto_sync_enabled, sync_interval_minutes
- last_sync, total_backups, total_size_mb

### Backups
- id, world_id, drive_file_id, filename
- size_mb, compressed, backup_type, status, error_message

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| 401 Unauthorized on agent | Ensure `auth_token` in config.json is valid |
| Auto-sync not working | Set `local_path` on world in frontend first |
| Upload fails | Check `TEMP_UPLOAD_DIR` exists and is writable |
| CORS errors | Ensure `ALLOWED_ORIGINS` matches frontend URL |
| Token refresh fails | User may need to re-login via frontend |

---

## For Production Deployment

See `PRODUCTION_READY.md` for:
- PostgreSQL migration
- API key authentication for agent
- Rate limiting
- Docker/Kubernetes deployment
- Monitoring & logging
- CI/CD pipeline

---

## For Code Refactoring

See `CODE_OPTIMIZATION.md` for:
- File structure improvements
- Code reduction opportunities
- Maintainability enhancements