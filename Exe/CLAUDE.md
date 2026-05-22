DO NOT RUN THE CODE , I WILL RUN IT MYSELF TO CHECK , JUST MAKE CODE CHANGEs.

This project contains the desktop app for Minecraft Backup.

---

## Project Structure

```
Exe/
├── desktop-app/             # Desktop app — FastAPI + vanilla JS SPA
│   ├── main.py              # Entry point (lifecycle, watcher, server)
│   ├── build.spec           # PyInstaller build config
│   ├── requirements.txt
│   ├── app/                 # Backend: config, models, routers, services
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── dependencies.py
│   │   ├── encryption.py
│   │   ├── server.py
│   │   ├── routers/         # auth.py, worlds.py, drive.py
│   │   └── services/        # google_drive_service.py
│   ├── static/              # Frontend (vanilla JS — NOT React)
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   ├── watcher/             # File system watcher
│   │   ├── __init__.py
│   │   └── watcher.py
│   └── docs/                # Documentation
└── .md/                     # Exe-specific docs
```

## Setup & Run

```bash
cd Exe/desktop-app
cp .env.example .env
# Fill in Google OAuth credentials
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
# Opens at http://127.0.0.1:8710
```

## Build

```bash
cd Exe/desktop-app
pyinstaller build.spec
# Output: dist/MinecraftBackup.exe
```

## Design System: Minecraft Pixel Theme

The frontend (`desktop-app/static/`) uses a Minecraft pixel theme.

### Colors (DO NOT revert to emerald/slate)
| Token | Hex | Usage |
|-------|-----|-------|
| mc-sky | `#5CACED` | Primary accent, progress, active states |
| mc-cream | `#FAFBD3` | Text on dark, input backgrounds |
| mc-wood | `#C69F78` | Card/nav backgrounds |
| mc-darkwood | `#995A24` | Borders, dark accents, decorative |
| mc-grass (WCAG AA) | `#5D6B2E` | Primary buttons, success, badges |
| mc-sky-dark (WCAG AA) | `#2A6B99` | Secondary buttons, info toasts |

### Fonts (WCAG 1.4.4 compliant)
- **Headings / buttons:** `Press Start 2P` at min 13px
- **Body:** `VT323` at 20px
- **Badges:** 15px VT323

### Key CSS Classes
- `.pixel-card` / `.pixel-card-dark` — Cards with pixel borders
- `.pixel-btn` / `-primary` / `-secondary` / `-danger` — Pixel buttons
- `.pixel-input` — Pixel-styled inputs
- `.pixel-toggle` — Toggle switch
- `.pixel-table` — Pixel table
- `.pixel-badge` / `-green` / `-gray` — Status badges
- `.minecraft-bg-grid` — Dark bg with grid pattern
- `.text-shadow` — 2px black text shadow

### Important
- Frontend is **vanilla JS** in `static/` — NOT React
- `frontend_Assets/` at root is a React design reference for the web app, not for this project
- DO NOT change the WCAG-compliant color palette back to file defaults (emerald/slate)

## Key Architecture

### App Lifecycle
- Single-instance check via socket port (8710)
- Heartbeat every 3s from browser, 10s timeout kills process (300s during OAuth flow)
- No `beforeunload` handler — tab close kills server via heartbeat timeout only
- OAuth redirect to Google extends heartbeat timeout to 300s so the server stays alive
- Exe re-open with port in use → calls `/api/reload` to refocus browser tab

### Watcher
- watchdog observer per-world in background thread
- `_backing_up` flag prevents concurrent backups
- Debounce 10s default
- Persistent zip cache in `data/uploads/`

### Auth
- Google OAuth PKCE for web login
- JWT tokens for web sessions (7 day expiry)
- Device pairing for one-time API key provisioning (used by desktop agent)
