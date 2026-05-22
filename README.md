# Minecraft Backup

Automatically backs up your Minecraft worlds to Google Drive. No manual zipping, no remembering — just play and it's safe.

## Download

**[Download the latest EXE](https://github.com/5HAH33R/minecraft-backup-app/releases)** — run it, sign in with Google, add your world path. Done.

No Python or setup required. The EXE is a standalone desktop app.

## Features

- File watcher detects when you save your game and triggers a backup automatically
- Debounce timer waits 10 seconds after the last save — won't interrupt your play
- Uploads compressed worlds to your own Google Drive
- Per-world management — track multiple worlds in one dashboard
- Auto-cleanup keeps only the N most recent backups

## Build from Source

```bash
cd Exe/desktop-app
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your [Google OAuth credentials](https://console.cloud.google.com/apis/credentials).

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
Exe/desktop-app/       # Desktop app (FastAPI + vanilla JS)
Webapp/Backend/        # Web backend (FastAPI + React frontend)
Webapp/desktop-agent/  # CLI agent for headless setups
```

## License

MIT
