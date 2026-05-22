# Architecture

## Stack
- **Frontend:** React 18, CRA (react-scripts 5.0.1), Tailwind CSS, React Router v6
- **Backend:** FastAPI (Python 3.10+), SQLAlchemy 2.0, SQLite
- **Auth:** Google OAuth 2.0 (PKCE) + JWT tokens
- **Storage:** Google Drive API v3
- **Desktop Agent:** Python CLI with file system watcher (watchdog)

## System Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  React App  │────▶│  FastAPI     │────▶│  Google     │
│  (port 3000)│     │  (port 8000) │     │  Drive      │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  SQLite      │
                    │  Database    │
                    └──────────────┘

┌────────────────────┐
│  Desktop Agent     │────▶ API (same backend)
│  (file watcher)    │
└────────────────────┘
```

## Data Flow

1. **User authenticates** via Google OAuth (PKCE flow). Backend stores encrypted Drive credentials.
2. **User registers a world** (name, optional local path). Backend creates DB record + Drive folder.
3. **Manual backup:** User uploads a ZIP file via frontend → backend saves to temp → uploads to Drive → records in DB. Oldest backup is auto-deleted (keeps only 1 latest).
4. **Auto-backup:** Desktop agent watches file system changes → debounces 10s → zips world → uploads via API.
5. **Restore:** User gets download link from Drive.

## Key Backend Modules

| Module | Path | Purpose |
|--------|------|---------|
| `main.py` | `Backend/app/main.py` | FastAPI app setup, CORS, rate limiting, health checks |
| `config.py` | `Backend/app/config.py` | Pydantic settings (env vars) |
| `database.py` | `Backend/app/database.py` | SQLAlchemy engine, session, base |
| `dependencies.py` | `Backend/app/dependencies.py` | Auth dependency (JWT + API key) |
| `models/` | `Backend/app/models/` | User, World, Backup, PairingCode ORMs |
| `routers/auth.py` | `Backend/app/routers/auth.py` | Google OAuth, login, user info |
| `routers/worlds.py` | `Backend/app/routers/worlds.py` | CRUD for worlds |
| `routers/drive.py` | `Backend/app/routers/drive.py` | Backup upload/download/delete, storage info |
| `routers/pairing.py` | `Backend/app/routers/pairing.py` | Desktop agent pairing code flow |
| `routers/refresh.py` | `Backend/app/routers/refresh.py` | JWT refresh token endpoint |
| `services/google_drive_service.py` | `Backend/app/services/` | Google Drive API wrapper |
| `utils/encryption.py` | `Backend/app/utils/` | Fernet encryption for stored credentials |

## Frontend Structure

| Component | Path | Purpose |
|-----------|------|---------|
| `App.js` | `src/App.js` | Router, AuthCallback, PrivateRoute |
| `AuthContext.js` | `src/contexts/AuthContext.js` | Auth state, login/logout |
| `ThemeContext.js` | `src/contexts/ThemeContext.js` | Dark/light mode toggle |
| `api.js` | `src/services/api.js` | Axios instance with JWT interceptor |
| `driveAPI.js` | `src/services/driveAPI.js` | World & Drive API wrappers |
| `pages/login.js` | `src/pages/` | Google sign-in |
| `pages/dashboard.js` | `src/pages/` | World list with search |
| `pages/AddWorld.js` | `src/pages/` | Create world form |
| `pages/WorldDetails.js` | `src/pages/` | World detail, upload, backup history |
| `pages/Settings.js` | `src/pages/` | Account, backup settings, desktop pairing |
| `components/` | `src/components/` | Shared UI: WorldCard, Navbar, StorageWidget, etc. |

## Desktop Agent

Python CLI (`desktop-agent/main.py`) that:
- Watches Minecraft save folders for changes using `watchdog`
- Debounces file changes (default 10s)
- Zips and uploads via API with JWT or API key auth
- Supports pairing flow (`--pair` flag) for hands-free auth
- Syncs world list periodically from API
