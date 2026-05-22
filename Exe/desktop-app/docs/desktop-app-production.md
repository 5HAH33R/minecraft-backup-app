# Production Readiness — Desktop App

Audit date: 2026-05-18
App: `Exe/desktop-app/`

---

## ✅ Fixed This Session

| Issue | File | Fix |
|---|---|---|
| `datetime.utcnow()` deprecated | All Python files | Replaced with `datetime.now(UTC)` |
| Backup count shows -1 | `app/routers/drive.py:114` | Added `world.total_backups += 1` on upload |
| Watcher not started | `main.py:105-131` | Integrated `BackupWatcher` into server startup |
| Dashboard stats not updating live | `static/app.js:409` | Added 5s auto-refresh when auto-sync is on |
| SECRET_KEY empty = broken encryption | `app/config.py:17-20` | Auto-generates temp key if `.env` is missing |
| Profile picture XSS (2 locations) | `static/app.js:145,642` | Wrapped `img src` in `escHtml()` |
| Confirm dialog Cancel never resolves | `static/app.js:93-99` | Cancel button now calls `resolve(false)` |
| Preferences never save | `static/app.js:701-706` | Wired up `PATCH /api/auth/preferences` call |
| SQLite concurrent write contention | `app/database.py:12-18` | Enabled WAL mode + busy timeout |
| Auto-refresh races with itself | `static/app.js:412-414` | Added `refreshing` guard flag |
| OAuth state memory leak | `app/routers/auth.py:49-57` | Expires stale states > 5 min |
| No rollback in watcher on failure | `main.py:97` | Added `db.rollback()` |
| `dir()` fragility in watcher cleanup | `main.py:100` | Changed to `locals()` |

---

## 🔴 Must Fix Before Ship

### 1. OAuth tokens leak in URL
**File:** `app/routers/auth.py:158`
**Problem:** `access_token` and `refresh_token` are in the redirect URL query string. Browser history, Referer headers, and logs capture them.
**Fix:** Use `window.location.hash` instead of query params, or exchange an ephemeral session code on the server side instead of passing tokens through the URL.

### 2. Tokens stored in localStorage
**File:** `static/app.js:113-114`
**Problem:** JWT and refresh tokens in `localStorage` are accessible to any JS. Any XSS yields full account takeover.
**Fix:** Use an in-memory variable with a short-lived httpOnly session cookie for server-to-server refresh. Or accept the risk (this is a local desktop app — the token is only accessible to code running on the user's own machine).

### 3. No graceful shutdown
**File:** `main.py:143-148`
**Problem:** `sys.exit(0)` kills in-flight backup uploads mid-execution. Daemon threads (watcher backups) are terminated immediately, leaving temp files and inconsistent DB state.
**Fix:** Replace `sys.exit()` with `uvicorn` shutdown events. Add a `shutdown_event` that sets a flag, signals the watcher, and waits for in-flight backups to complete (up to a timeout).

### 4. Logging is all `print()`
**Files:** `main.py`, `watcher/watcher.py`, `app/services/google_drive_service.py`
**Problem:** No log levels, no file output, no timestamps. Production debugging is impossible.
**Fix:** Replace all `print()` with Python's `logging` module. Configure file + console handlers with rotation in `main.py`.

---

## 🟡 Should Fix Before Ship

### 5. Backup listing has no pagination
**File:** `app/routers/drive.py:155`
**Problem:** Returns ALL backups. A world with hundreds of backups sends a massive response over the local API.
**Fix:** Add `?limit=50&offset=` query params with a default limit.

### 6. Temp files on crash
**File:** `main.py:62-64`
**Problem:** ZIP files created in temp dir during auto-backup are only cleaned up in `finally`. A hard crash before `finally` orphans them permanently.
**Fix:** Store temp files in `TEMP_UPLOAD_DIR` and clean on startup. Or register an `atexit` handler.

### 7. Settings page shows stale user data
**File:** `static/app.js:634-638`
**Problem:** Settings fetches user data with a silent `catch` that swallows errors. The initial avatar/name comes from `state.user` (loaded at login), but it's never refreshed after a server restart.
**Fix:** Move the `state.user` update to happen **before** rendering the account section.

---

## 🟢 Nice to Have

- Replace vanilla JS frontend with the React app (build to static files, serve from FastAPI)
- Add restore functionality (download + extract backup back to saves folder)
- Package with PyInstaller for a single executable (no Python dependency for end users)
- Add system tray icon with background running state
- Add backup retention UI (number of backups to keep per world)
- Switch from JWT to session cookies for better security
- Add CSRF token for the upload endpoint

---

## How to Ship Today

The app works for a single user on their local machine. The critical security issues (token in URL, localStorage) are acceptable for a local desktop app — unlike a web app, an attacker would already need code execution on the user's machine to exploit them.

**Minimum viable ship checklist:**
1. ⬜ User must set up `.env` with Google OAuth credentials
2. ⬜ User must add `http://localhost:8710/api/auth/google/callback` to Google Cloud Console
3. ⬜ Run `python main.py` — opens `http://localhost:8710`
4. ⬜ Sign in with Google, create a world, upload a backup
5. ⬜ Enable auto-sync and verify watcher detects file changes
6. ⬜ Delete a backup, verify count doesn't go negative
7. ⬜ Settings → change preferences, verify they persist
