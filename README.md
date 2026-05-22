# Minecraft Backup

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

I lost my Minecraft world of 3 years to a corrupted save file. This app makes sure that never happens to anyone else.

It watches your Minecraft save folder and automatically uploads fresh backups to Google Drive. No manual zipping. No remembering. Just play and it's safe.

## Download

**[Download the latest EXE](https://github.com/5HAH33R/minecraft-backup-app/releases)** — run it, sign in with Google, add your world path. Done.

No Python or setup required. The EXE is a standalone desktop app with a Minecraft-themed UI.

## How It Works

```
You save your game
       │
       ▼
File watcher detects changes
       │
       ▼
Debounce timer (10s) waits for saves to finish
       │
       ▼
World folder is compressed to .zip
       │
       ▼
Uploaded to your Google Drive
       │
       ▼
Stored at: MinecraftBackups/{World Name}/{timestamp}.zip
```

The app runs in the background — open it, add your world path, and it handles the rest.

## Features

### Automatic File Watching
Uses watchdog to monitor your Minecraft save folder for any file changes. When you save your game, the watcher detects it instantly.

### Smart Debounce
Waits 10 seconds after the last file change before triggering a backup. This prevents uploading mid-save or during autosaves. You won't even notice it running.

### Google Drive Cloud Storage
Backups are uploaded to your own Google Drive — not some third-party server. Your worlds stay under your control. Each world gets its own organized folder.

### Per-World Management
Add multiple worlds, each with its own:
- Display name and description
- Local save folder path
- Auto-sync toggle
- Backup history and download links

### Auto-Cleanup
Keeps only the N most recent backups per world (configurable). Old backups are automatically deleted so your Drive doesn't fill up.

### Minecraft Pixel Theme
Desktop app features a custom Minecraft-inspired UI (Press Start 2P font, grass/wood/sky color palette). Looks like it belongs in the game.

### Manual Backups
Trigger a backup anytime, even when auto-sync is disabled. Download or delete individual backups from the dashboard.

## Setup

### Desktop App (Recommended)

1. Download the latest EXE from [Releases](https://github.com/5HAH33R/minecraft-backup-app/releases)
2. Run it — sign in with your Google account
3. Click **Add World** and point it to your Minecraft saves folder
4. That's it. Backups run automatically from here.

Your saves are typically at:
- Windows: `%appdata%\.minecraft\saves`
- macOS: `~/Library/Application Support/minecraft/saves`
- Linux: `~/.minecraft/saves`

### Web App

The web backend has a full React frontend and FastAPI backend:

```bash
cd Webapp/frontend
npm install
npm start
# Opens at http://localhost:3000
```

```bash
cd Webapp/Backend
pip install -r requirements.txt
cp .env.example .env  # Fill in your Google OAuth credentials
python -m app.main
# Runs at http://localhost:8000
```

### Desktop Agent (Headless)

A CLI agent for servers or headless setups that watches worlds and uploads via the web backend:

```bash
cd Webapp/desktop-agent
pip install -r requirements.txt
python main.py --help
```

## Build from Source

### Desktop App

```bash
cd Exe/desktop-app
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your [Google OAuth credentials](https://console.cloud.google.com/apis/credentials). You need a Google Cloud project with the Drive API enabled.

```bash
python main.py
# Opens at http://127.0.0.1:8710
```

To build the EXE yourself:

```bash
pyinstaller build.spec
# Output: dist/MinecraftBackup.exe
```

## Project Structure

```
Exe/desktop-app/          # Desktop app (FastAPI + vanilla JS)
  ├── main.py             # Entry point
  ├── app/                # Backend: config, models, routes, services
  ├── static/             # Frontend: HTML, JS, CSS
  ├── watcher/            # File system watcher
  └── build.spec          # PyInstaller build config

Webapp/Backend/           # Web backend (FastAPI + SQLite)
  ├── app/                # Routes, models, services
  └── requirements.txt

Webapp/frontend/          # Web frontend (React + Tailwind)
  ├── src/                # Components, pages, contexts
  └── tailwind.config.js

Webapp/desktop-agent/     # CLI agent for headless backup
  ├── main.py
  └── config.example.json
```

## Tech Stack

| Component | Stack |
|-----------|-------|
| Desktop backend | Python, FastAPI, Uvicorn |
| Desktop frontend | Vanilla JavaScript, CSS (Minecraft Pixel Theme) |
| Web backend | Python, FastAPI, SQLAlchemy |
| Web frontend | React, Tailwind CSS |
| Database | SQLite |
| Cloud storage | Google Drive API v3 |
| Auth | Google OAuth 2.0 (PKCE), JWT |
| File watcher | watchdog |
| Packaging | PyInstaller |

## Security

- Google OAuth tokens are encrypted with Fernet (AES) before storage
- JWT tokens with 7-day expiry
- Rate limiting on all endpoints
- No credentials in source code (use `.env`)

## License

MIT
