# Minecraft Backup App — Design Guide

## 1. Project Overview

A self-hosted application for backing up Minecraft worlds to Google Drive. Users authenticate via Google OAuth, register worlds with optional local paths, and rely on a desktop agent for automatic file-watching backups. The frontend uses a Minecraft-inspired pixel aesthetic.

### Core User Stories

- As a player, I want to back up my Minecraft worlds to Google Drive automatically.
- As a player, I want to see all my worlds and their backup status on a dashboard.
- As a player, I want to download or delete individual backups.
- As a player, I want to set up the desktop agent once with a pairing code and never think about it again.

---

## 2. System Architecture

```
+-------------------+       +-------------------+       +-------------------+
|   Desktop Agent   | ----> |   FastAPI Backend  | ----> |  Google Drive API |
| (Python/Watchdog) | REST  |   (Python/FastAPI) |  v3   |  (Cloud Storage)  |
|                   |       |                    |       |                   |
| - File watcher    |       | - Auth (JWT/OAuth) |       | - World backups   |
| - API key auth    |       | - API key/pair     |       |   as ZIP files    |
| - Debounced sync  |       | - Rate limiting    |       |                   |
+-------------------+       | - Encrypted store  |       +-------------------+
        ^                   | - Drive service    |
        |                   +---------+----------+
        |                             |
        |   Pairing code              |
        |   (one-time)                |
        |                             v
+-------------------+       +-------------------+
|   React Frontend  |       |   SQLite Database |
|   (Tailwind CSS)  |       |                   |
|                   |       | - users           |
| - Dashboard       |       | - worlds          |
| - World CRUD      |       | - backups         |
| - Settings/pair   |       | - pairing_codes   |
| - Dark mode       |       +-------------------+
| - Pixel aesthetic |
+-------------------+
```

### Data Flow

1. **User logs in** via frontend → Google OAuth with PKCE → backend returns JWT + refresh_token
2. **User pairs desktop agent** from Settings → backend generates 6-char code → agent exchanges it for `mba_*` API key
3. **Agent watches files** via watchdog → detects changes → debounces (10s default) → zips world folder → uploads via REST
4. **Backend receives backup** → saves temp file → uploads to Google Drive → deletes previous backup (keep-latest) → records in DB

---

## 3. Tech Stack

### Backend

| Technology | Purpose | Version |
|---|---|---|
| Python / FastAPI | REST API framework | 0.104.1 |
| SQLAlchemy | ORM | 2.0.23 |
| SQLite (dev) → PostgreSQL (prod) | Database | — |
| Alembic | Migrations | 1.13.0 |
| Google API Python Client | Drive v3 API | 2.111.0 |
| python-jose | JWT encode/decode (HS256) | 3.3.0 |
| cryptography (Fernet) | Encrypt credentials at rest | 41.0.7 |
| slowapi | Rate limiting | — |
| pydantic-settings | Config from .env | 2.1.0 |
| uvicorn | ASGI server | 0.24.0 |

### Frontend

| Technology | Purpose |
|---|---|
| React 18 | UI framework |
| React Router v6 | Client-side routing |
| Axios | HTTP client with interceptors |
| Tailwind CSS 3 | Utility-first styling |
| Press Start 2P | Minecraft pixel font (Google Fonts) |
| react-toastify | Toast notifications |

### Desktop Agent

| Technology | Purpose |
|---|---|
| watchdog 3.0.0 | File system monitoring |
| requests 2.31.0 | HTTP client |

---

## 4. Project Structure

```
minecraft-backup-app/
├── Backend/app/
│   ├── main.py              # FastAPI app, router registration, health endpoints
│   ├── config.py            # Pydantic Settings from .env
│   ├── database.py          # SQLAlchemy engine, session, Base
│   ├── dependencies.py      # get_current_user (JWT + X-API-Key)
│   ├── models/
│   │   ├── user.py          # User, World, Backup ORM models
│   │   └── pairing_code.py  # PairingCode model
│   ├── routers/
│   │   ├── auth.py          # Google OAuth + PKCE login flow
│   │   ├── worlds.py        # World CRUD
│   │   ├── drive.py         # Backup upload/download/delete + storage info
│   │   ├── api_keys.py      # API key CRUD (hashed with SHA-256)
│   │   ├── refresh.py       # JWT refresh token exchange
│   │   └── pairing.py       # Device pairing code endpoints
│   ├── schemas/
│   │   └── world.py         # Pydantic request/response schemas
│   ├── services/
│   │   └── google_drive_service.py  # Drive API wrapper (upload, list, delete)
│   └── utils/
│       └── encryption.py    # Fernet encrypt/decrypt for stored credentials
├── frontend/src/
│   ├── App.js               # Router + AuthCallback + PrivateRoute
│   ├── index.css            # Pixel utility classes, font import
│   ├── tailwind.config.js   # Custom colors (mc-*), pixel font
│   ├── components/          # Navbar, WorldCard, StorageWidget, etc.
│   ├── pages/               # Login, Dashboard, AddWorld, WorldDetails, Settings
│   ├── contexts/            # AuthContext, ThemeContext
│   └── services/            # api.js (Axios), driveAPI.js (API wrappers)
├── desktop-agent/
│   ├── main.py              # Watchdog monitor, backup loop, CLI args
│   └── config.json          # Agent configuration
└── .md/                     # Documentation
```

---

## 5. Design System — Minecraft Pixel Theme

### Core Design Values

- **Playful but functional** — pixel borders and blocky buttons without sacrificing usability
- **Minecraft-inspired** — color palette from blocks, not a literal game UI
- **Dark-first** — both light and dark modes, dark is the default experience

### Color Palette

| Token | Hex | Usage |
|---|---|---|
| `mc-grass` | `#7CB342` | Success, confirm actions, paired status |
| `mc-dirt` | `#8D6E63` | Navbar background, secondary elements |
| `mc-stone` | `#9E9E9E` | Borders, neutral accents |
| `mc-wood` | `#A1887F` | Cards, container backgrounds |
| `mc-sky` | `#64B5F6` | Links, info, primary actions |
| `mc-gold` | `#FFD54F` | Warnings, highlights |
| `mc-obsidian` | `#263238` | Dark mode backgrounds |

### Typography

| Usage | Font |
|---|---|
| **Headings** | `Press Start 2P` (monospace, pixel font) |
| **Body text** | System font stack (Segoe UI, sans-serif) |
| **Code** | `source-code-pro, monospace` |

### Custom CSS Utilities

```css
/* Blocky card/container border */
.pixel-borders {
  border: 4px solid #5D4037;
  box-shadow: 4px 4px 0px 0px rgba(0,0,0,0.3);
}
.dark .pixel-borders {
  border-color: #37474F;
}

/* Button with press-down effect */
.pixel-btn {
  border: 3px solid currentColor;
  box-shadow: 3px 3px 0px 0px rgba(0,0,0,0.3);
  transition: all 0.05s linear;
}
.pixel-btn:active {
  transform: translate(3px, 3px);
  box-shadow: none;
}
```

### Dark Mode

- Implemented via `class` strategy: toggle `dark` class on `<html>`
- Default reads from `localStorage('theme')`, falls back to `prefers-color-scheme`
- All components use Tailwind `dark:` variants
- Context: `ThemeContext` provides `{ theme, toggleTheme }`
- Persistent: saves choice to localStorage

### Toast Notifications

- `react-toastify` at bottom-right corner
- 3-second auto-close, newest on top
- Used for all success/error/info feedback

---

## 6. Authentication System

### Web Login Flow (Google OAuth + PKCE)

```
Frontend                        Backend                     Google
   |                               |                          |
   |  GET /api/auth/google/login   |                          |
   |------------------------------>|                          |
   |  { auth_url }                 |  Generate PKCE verifier  |
   |<------------------------------|  + challenge, store state |
   |                               |                          |
   |  Redirect to auth_url         |                          |
   |------------------------------------------------------->|
   |                               |                          |
   |  User authorizes              |                          |
   |<-------------------------------------------------------|
   |                               |                          |
   |  GET /api/auth/google/callback?code=...&state=...       |
   |------------------------------>|                          |
   |  Redirect to /auth/callback   |  Exchange code,          |
   |  ?token=JWT&refresh_token=XYZ |  create/update user,     |
   |<------------------------------|  encrypt Google creds    |
   |                               |                          |
   |  Store token + refresh_token  |                          |
   |  in localStorage              |                          |
```

### Desktop Agent Auth — Device Pairing

```
Frontend Settings               Backend                   Desktop Agent
   |                               |                          |
   |  POST /api/auth/pair          |                          |
   |  (JWT Bearer)                 |                          |
   |------------------------------>|                          |
   |  { code: "ABC123" }          |  Generate 6-char code,   |
   |<------------------------------|  store in pairing_codes  |
   |                               |                          |
   |  Show code to user            |                          |
   |------- (user reads code) ----------> python --pair ABC123|
   |                               |                          |
   |                               |  POST /pair/exchange      |
   |                               |  { code: "ABC123" }      |
   |                               |<-------------------------|
   |                               |  { api_key: "mba_..." }  |
   |                               |------------------------->|
   |                               |                     Save to config.json
   |                               |                          |
   |  GET /pair/status (poll 3s)   |                          |
   |------------------------------>|                          |
   |  { paired: true }            |                          |
   |<------------------------------|                          |
```

### Dual Auth Resolution (dependencies.py)

```
Request comes in
    │
    ├── Has X-API-Key header? → SHA-256 hash it → query User.api_key_hash
    │     └── Match? → return User
    │     └── No match → 401
    │
    └── Has Authorization: Bearer? → decode JWT (HS256) → extract sub → query User.id
          └── Valid → return User
          └── Invalid → 401
```

### Key Design Decisions

- API keys use SHA-256 hashing (never stored in plaintext)
- JWT expiry is 7 days (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh tokens are encrypted with Fernet before storage
- API keys never expire — revoke via Settings page
- Rate limits: 10/min for auth, 20/min for uploads, 100/min for general API

---

## 7. Data Models

### User

| Column | Type | Notes |
|---|---|---|
| id | PK Integer | |
| email | String, unique, NOT NULL | From Google profile |
| google_id | String, unique, NOT NULL | Google's user ID |
| google_credentials | Text, NOT NULL | Encrypted OAuth tokens (Fernet) |
| drive_folder_id | String | Google Drive "MinecraftBackups" folder ID |
| api_key_hash | String, unique | SHA-256 of API key, nullable |
| refresh_token | Text | Encrypted, nullable |
| auto_cleanup_enabled | Boolean | Default true |
| max_backups_per_world | Integer | Default 10 |

### World

| Column | Type | Notes |
|---|---|---|
| id | PK Integer | |
| user_id | FK → users.id | |
| name | String, NOT NULL | World display name |
| description | Text | Optional |
| local_path | String | Path on disk for auto-sync |
| drive_folder_id | String | Google Drive subfolder ID |
| auto_sync_enabled | Boolean | Default false |
| sync_interval_minutes | Integer | Default 60 |
| total_backups | Integer | Count |
| total_size_mb | Float | Sum of backup sizes |

### Backup

| Column | Type | Notes |
|---|---|---|
| id | PK Integer | |
| world_id | FK → worlds.id | |
| drive_file_id | String, unique | Google Drive file ID |
| filename | String | Format: `{world}_{YYYY-MM-dd_HH-MM-SS}.zip` |
| size_mb | Float | |
| backup_type | String | `"manual"` or `"auto"` |
| status | String | `"completed"` or `"failed"` |

### PairingCode

| Column | Type | Notes |
|---|---|---|
| id | PK Integer | |
| user_id | FK → users.id | |
| code | String, unique | 6-char alphanumeric, uppercase |
| expires_at | DateTime | 5 minutes from creation |
| used | Boolean | Default false |

---

## 8. API Endpoints

### Auth (`/api/auth`)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/google/login` | None | Returns Google OAuth URL with PKCE params |
| GET | `/google/callback` | None | OAuth callback → creates user, returns JWT redirect |
| GET | `/me` | JWT | Current user profile |
| POST | `/logout` | JWT | Logout confirmation |
| POST | `/refresh` | None | Exchange refresh_token for new JWT |

### API Keys (`/api/auth/api-keys`)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `` | JWT | Create `mba_*` API key |
| GET | `` | JWT | Check if key exists |
| DELETE | `` | JWT | Revoke key |

### Pairing (`/api/auth/pair`)
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/pair` | JWT | Generate 6-char pairing code (5min expiry) |
| POST | `/pair/exchange` | None | Exchange code for API key |
| GET | `/pair/status` | JWT | Check if paired |

### Worlds (`/api/worlds`)
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `` | JWT | List all worlds for current user |
| POST | `` | JWT | Create world |
| GET | `/{id}` | JWT | Get world details |
| PUT | `/{id}` | JWT | Update world (incl. auto_sync, local_path) |
| DELETE | `/{id}` | JWT | Delete world (not Drive files) |

### Drive (`/api/drive`)
| Method | Path | Auth | Rate Limit |
|---|---|---|---|
| POST | `/worlds/{id}/backup` | JWT/API Key | 20/min |
| GET | `/worlds/{id}/backups` | JWT | 100/min |
| GET | `/worlds/{id}/backups/{bid}/download-link` | JWT | 100/min |
| DELETE | `/worlds/{id}/backups/{bid}` | JWT | 100/min |
| GET | `/storage` | JWT | 100/min |

### Health
| Method | Path | Description |
|---|---|---|
| GET | `/health` | Basic health |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe (checks DB) |

---

## 9. Desktop Agent Architecture

### Startup Flow

```
Parse CLI args (--config, --api-url, --debug, --pair)
    │
    ├── --pair CODE → POST /api/auth/pair/exchange → save api_key → exit
    │
    └── Normal start:
         │
         ├── Has api_key in config? → Use X-API-Key header
         ├── Has auth_token? → Use Bearer JWT (legacy fallback)
         └── Neither? → Print error, exit
         │
         └── agent.start()
              │
              ├── sync_with_api() → GET /api/worlds → start file watchers
              └── main_loop() → every 1s: check debounced backups, periodic re-sync
```

### Backup Cycle

```
Watchdog detects file change
    → _trigger_backup(): sets backup_pending = True, records last_modified
    → main_loop(): checks backup_pending + debounce timeout
        → sets backup_pending = False
        → starts backup_world thread
            → adds world to active_backups
            → zips world folder to ~/.minecraft_backup/temp/
            → uploads via POST /api/drive/worlds/{id}/backup
            → removes from active_backups
            → resets backup_pending = False (overrides any events during backup)
```

### Config Schema (config.json)

```json
{
  "api_url": "http://localhost:8000",
  "api_key": "mba_...",
  "auth_token": "eyJ...",
  "refresh_token": "...",
  "minecraft_saves_path": "...",
  "watched_worlds": [...],
  "sync_interval_minutes": 30,
  "debounce_seconds": 10,
  "debug": false
}
```

### Key Design Decisions

- **API key preferred over JWT** — keys don't expire, no refresh needed
- **Backward compatible** — JWT + refresh token flow still works if no API key configured
- **Debounce** — 10s default, prevents rapid backups during active play
- **Active backup guard** — `active_backups` set prevents concurrent backups of same world
- **Backup-pending reset** — `backup_pending` is reset in the `finally` block to prevent double backups from watchdog events triggered during the zip/upload process

---

## 10. Security Architecture

### Encryption

| What | How | Key Source |
|---|---|---|
| Google OAuth credentials | Fernet (symmetric) | SHA-256 of SECRET_KEY |
| Refresh tokens | Fernet | Same key |
| API keys | SHA-256 hash (one-way) | No reversibility — hash comparison only |

### Authentication

| Method | Where | Expiry |
|---|---|---|
| JWT Bearer | Frontend web app | 7 days |
| X-API-Key | Desktop agent | Never (until revoked) |
| Refresh token | Token refresh endpoint | Until revoked |

### Rate Limiting

| Endpoint Group | Limit |
|---|---|
| Auth (login, callback, refresh, pair) | 10/minute |
| API key operations | 10/minute |
| Backup uploads | 20/minute |
| All other endpoints | 100/minute |

### OAuth Security

- PKCE (Proof Key for Code Exchange) enforced for Google OAuth
- State parameter validated on callback
- Offline access with consent prompt forces refresh token issuance

---

## 11. Backup Retention

The app uses a **keep-latest** strategy:

1. When a new backup is created, the previous backup (if any) is deleted from Drive
2. Only the latest backup per world is retained at any time
3. The backup count in the DB stays at 1 (it's a replace operation)
4. A background cleanup job can delete excess backups beyond the configured `max_backups_per_world`

### Filename Convention

`{world_name}_{YYYY-MM-dd_HH-MM-SS}.zip`

Example: `My Survival World_2026-05-18_14-30-22.zip`

---

## 12. Environment & Configuration

### Backend (.env)

```
SECRET_KEY=<random-string-min-32-chars>
GOOGLE_CLIENT_ID=<google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<google-oauth-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
DATABASE_URL=sqlite:///./minecraft_backup.db
ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend (.env)

```
REACT_APP_API_URL=http://localhost:8000
```

### Desktop Agent (config.json)

See Section 9 for full schema. Can also pass `--api-url` and `--debug` as CLI args.

---

## 13. Development Conventions

### Code Style

- Python: PEP 8, type hints on function signatures
- JavaScript: ES6+ with React hooks (functional components, no class components)
- Backend routers: each file is a self-contained router module with docstrings on public endpoints
- Frontend pages and components: one file per component, same name as the component

### File Organization Rules

- Models in `models/`, routers in `routers/`, schemas in `schemas/`
- Frontend: pages in `pages/`, shared components in `components/`, contexts in `contexts/`
- Keep files under 500 lines
- No secrets, credentials, or .env files committed

### Validation Boundaries

- Pydantic schemas validate at the API boundary (router layer)
- Desktop agent validates config at load time
- Frontend validates form inputs before sending

### Error Handling

- Backend: HTTPException with clear detail messages
- Desktop agent: try/except around file operations (PermissionError, OSError), logged to both file and console
- Frontend: toast notifications for user-facing errors

---

## 14. Testing & Deployment

### Current State
- **Database:** SQLite (dev), PostgreSQL planned
- **Migrations:** Alembic configured, initial migration pending
- **Tests:** Not yet implemented
- **Containerization:** Docker not yet set up
- **CI/CD:** Not yet set up

### Planned Infrastructure
- Docker Compose for local development (backend, frontend, PostgreSQL)
- Multi-stage Dockerfiles for production builds
- GitHub Actions CI pipeline
- Kubernetes manifests (optional)

### Monitoring (Planned)
- Sentry for error tracking
- Prometheus metrics
- Structured logging (structlog)

---

## 15. Design Decisions — Rationale

### Why API keys over long-lived JWT for the desktop agent?
JWT tokens expire. Having the agent manage token refresh adds complexity and a failure point. API keys never expire, are revocable, and use the same auth path (`get_current_user` handles both Bearer and X-API-Key transparently).

### Why device pairing over copying tokens?
No manual credential handling. The user types a short code printed on screen. The exchange is one-directional — the agent never sees the user's long-lived Google refresh token.

### Why keep-latest backup strategy?
Minecraft worlds are small (typically <100MB zipped). Keeping one backup per world minimizes Drive storage usage while still providing rollback capability. Users who want more can adjust `max_backups_per_world`.

### Why SHA-256 for API keys instead of bcrypt?
API keys are already high-entropy random strings (`mba_` + 32-byte urlsafe token). They don't benefit from bcrypt's work factor. SHA-256 is fast and deterministic (important for lookups — we need to find the user by key hash, not just verify against a known user).

### Why pixel theme?
The app manages Minecraft worlds. The pixel aesthetic reinforces the Minecraft connection and makes the app feel like part of the game ecosystem rather than a generic admin tool.

### Why SQLite in development?
Zero configuration, fast iteration. The ORM abstraction (SQLAlchemy) means switching to PostgreSQL for production requires only changing `DATABASE_URL` and removing SQLite-specific `check_same_thread` args.
