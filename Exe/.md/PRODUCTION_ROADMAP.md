# Desktop App — Production Roadmap

This file covers all remaining tasks for the desktop app (`Exe/desktop-app/`).

---

## Current State

### ✅ Completed Features
- Minecraft Pixel Theme frontend (vanilla JS, WCAG AA compliant)
- Google OAuth authentication (PKCE)
- World CRUD
- Backup upload to Google Drive
- Auto-backup via watchdog file watcher (single-instance guard)
- API key + device pairing for desktop agent
- JWT refresh tokens
- Single-instance detection (socket port check)
- Auto-shutdown on tab close (heartbeat + beforeunload)
- App lifecycle: exe re-open brings browser to front
- Persistent zip cache in `data/uploads/` (survives temp dir cleanup)
- Status auto-reset from "completed" → "idle" after 5s
- Upload progress bar (XHR-based)
- Backup retention settings UI (auto-cleanup toggle + max backup count)

### 📁 Project Structure
```
Exe/
├── desktop-app/             (Desktop app — FastAPI + vanilla JS)
│   ├── main.py              (Entry point, lifecycle, watcher start)
│   ├── build.spec           (PyInstaller config)
│   ├── app/                 (Backend: config, models, routers, services)
│   ├── static/              (Frontend: index.html, app.js, style.css)
│   ├── watcher/             (File system watcher)
│   └── docs/                (Documentation)
└── .md/                     (Exe-specific documentation)
```

---

## Audit Findings — 2026-05-19

### 🔴 Security: Critical / High

#### 1. Embedded Google OAuth credentials in source code
**File:** `app/config.py:13-14` — `_EMBEDDED_GOOGLE_CLIENT_ID` and `_EMBEDDED_GOOGLE_CLIENT_SECRET` are hardcoded and committed to git. While desktop apps commonly embed OAuth creds, these are visible in the source repo.

#### 2. OAuth tokens in URL query string
**File:** `app/routers/auth.py:160` — `redirect_url = f"/?token={access_token}&refresh_token={refresh_token_raw}"`. Tokens are passed via URL query params, visible in browser history, server access logs, and potentially leaked via Referer header.

#### 3. Tokens stored in localStorage
**File:** `static/app.js:861-871` — JWT access token and refresh token stored in `localStorage`. Accessible to any JS on the same origin. For a local-only app the risk is limited, but should use in-memory + httpOnly cookies if the architecture allows.

#### 4. Refresh token enumeration
**File:** `app/routers/auth.py:227-234` — The refresh endpoint iterates ALL users to find a matching refresh token (`for candidate in db.query(User).all()`). This is O(n) per request and creates a timing oracle. A `refresh_token_hash` column with index would fix this.

#### 5. `os._exit(0)` without graceful shutdown
**Files:** `main.py:120, 145, 149` — Multiple paths call `os._exit(0)` directly, which:
- Skips Python cleanup handlers
- Can corrupt SQLite (WAL checkpoint not finalized)
- Does not wait for in-flight backups
- Leaves temp files behind

#### 6. No CSRF protection
All API endpoints accept requests without CSRF tokens. A malicious page visited while the app is running could make credentialed requests.

### 🟡 Security: Medium

#### 7. No rate limiting on auth endpoints
`/auth/login` and `/auth/google/callback` have no rate limiting or brute-force protection.

#### 8. Zip slip vulnerability in `download_backup`
**File:** `app/services/google_drive_service.py:184` — `zipf.extractall(dest.parent)` extracts without path sanitization. A crafted backup with `../` paths could overwrite files outside the target directory.

#### 9. JWT key stored on disk
**File:** `app/config.py:90-91` — `SECRET_KEY` persisted to `data/secret.key` in plaintext. If an attacker gains filesystem access, they can forge JWTs.

#### 10. No input validation in `update_preferences`
**File:** `app/routers/auth.py:183-211` — Body is typed as `dict` and used directly without Pydantic model validation.

#### 11. `httpx.AsyncClient` created per request
**File:** `app/routers/auth.py:87, 99` — No connection pooling; each OAuth callback creates new clients.

### 🔵 Operational Issues

#### 12. No watcher health monitoring
If the `BackupWatcher` thread crashes, there's no mechanism to detect or restart it. The app continues running with no backups.

#### 13. Race condition in watcher flags
**File:** `watcher/watcher.py:29-38, 143-155` — `backup_pending` and `_backing_up` are modified with the lock held, but the state machine logic in `_run()` checks them together and could race during rapid file changes.

#### 14. Redundant `_backup_done` callback
**File:** `main.py:247` and `watcher/watcher.py:127-130` — `_backup_done` just discards from `_backup_running`, but `_run_backup` already clears `_backing_up` and `backup_pending` in its `finally` block. This creates a double-clear path.

#### 15. No Drive upload progress feedback
The XHR upload progress bar is for manual file uploads, but the watcher's auto-backup to Google Drive has no progress indication in the UI.

#### 16. In-memory OAuth state doesn't survive restart
**File:** `app/routers/auth.py:23` — `pending_auth_states` is in-memory only. If the app restarts during an OAuth flow, the user gets an error.

#### 17. No backup restore functionality
Users can download backup files but there's no "restore to saves folder" feature.

---

## Remaining Tasks

### Phase 1: Security Fixes (High Priority)

#### 1.1 OAuth & Token Handling
- [ ] Move tokens from URL query string to ephemeral session code (hash-based or POST-only exchange)
- [ ] Replace localStorage with in-memory session or httpOnly cookie approach
- [ ] Add `refresh_token_hash` column to `User` model with index, replace linear scan
- [ ] Remove embedded credentials from git (move to `.env` only, document setup)

#### 1.2 Graceful Shutdown
- [ ] Replace `os._exit(0)` with proper uvicorn lifecycle events
- [ ] Wait for in-flight backups to complete before exit
- [ ] Clean up temp files on shutdown
- [ ] Finalize SQLite WAL checkpoint on exit

#### 1.3 CSRF & Rate Limiting
- [ ] Add CSRF protection to all state-changing endpoints
- [ ] Add rate limiting to `/auth/login` and `/auth/google/callback`

### Phase 2: Polish & Stability (Medium Priority)

#### 2.1 Crash Recovery
- [ ] On restart: check if zip exists in `data/uploads/` before re-compressing
- [ ] Handle crash mid-upload (zip still exists, re-upload it from cache)
- [ ] Add watcher health monitoring + auto-restart on failure

#### 2.2 Watcher Fixes
- [ ] Fix lock race in watcher state machine (`backup_pending` / `_backing_up`)
- [ ] Remove redundant `_backup_done` callback — consolidate cleanup in `_run_backup`
- [ ] Add Drive upload progress feedback to status bar

#### 2.3 Build & Packaging
- [ ] Add app icon to `build.spec`
- [ ] Test PyInstaller build: `cd Exe/desktop-app && pyinstaller build.spec`
- [ ] Verify single exe works from any location

### Phase 3: Features (Low Priority)

#### 3.1 Restore Functionality
- [ ] Add "Restore" button on backup row
- [ ] Download backup from Drive, extract to saves folder
- [ ] Sanitize paths in `zipfile.extractall` to prevent zip slip

#### 3.2 System Tray
- [ ] Add system tray icon (requires pystray or PyQt)
- [ ] Minimize to tray on window close

### Phase 4: Testing & Operations (Low Priority)

#### 4.1 Connection & Resource Management
- [ ] Add `httpx.AsyncClient` connection pooling in auth router
- [ ] Add input validation via Pydantic model for `update_preferences`
- [ ] Add CORS middleware explicit configuration

#### 4.2 Manual Test Pass
- [ ] Verify single-instance detection works
- [ ] Verify auto-shutdown on tab close
- [ ] Verify exe re-open works
- [ ] Verify backup watcher detects changes
- [ ] Verify status transitions (idle -> backing up -> completed -> idle)

---

## Implementation Order

### Sprint 1: Security
1. Remove tokens from URL query string (hash/session exchange)
2. Replace localStorage with in-memory session
3. Indexed refresh token lookup
4. Graceful shutdown (replace os._exit)
5. CSRF protection + rate limiting
6. Remove embedded creds from git

### Sprint 2: Stability
7. Crash recovery (zip cache on restart)
8. Watcher health monitoring
9. Lock race fix + redundant callback removal
10. Drive upload progress in UI
11. httpx connection pooling + input validation

### Sprint 3: Features & Build
12. Restore functionality with zip slip protection
13. System tray icon
14. Build & packaging (icon, test PyInstaller)
15. Manual test pass

---

## Files to Modify

| File | Changes |
|------|---------|
| `desktop-app/app/config.py` | Remove embedded creds default, move to .env only |
| `desktop-app/app/routers/auth.py` | Token exchange flow, rate limiting, indexed refresh token |
| `desktop-app/app/models.py` | Add `refresh_token_hash` column |
| `desktop-app/app/dependencies.py` | CSRF dependency |
| `desktop-app/static/app.js` | localStorage → in-memory, session token exchange |
| `desktop-app/main.py` | Graceful shutdown, crash recovery, os._exit removal |
| `desktop-app/watcher/watcher.py` | Lock race fix, health monitoring, remove redundant callback |
| `desktop-app/app/services/google_drive_service.py` | Zip slip fix in `download_backup` |
| `desktop-app/build.spec` | App icon |
