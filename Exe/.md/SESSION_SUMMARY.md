# Session Summary — Desktop App (Exe)

**Last updated:** 2026-05-22

---

## ✅ Completed Work

### Desktop Agent Bug Fixes (`desktop-agent/main.py`)
- ✅ Fixed compression crash on locked files (PermissionError handling)
- ✅ Fixed `arcname` type (Path object to string conversion for Python compatibility)
- ✅ Added `on_created` and `on_deleted` event handlers
- ✅ Fixed "lost changes" bug during backup (changes now tracked during upload)
- ✅ Changed config file path from `~/.minecraft_backup/config.json` to `./config.json`

### Desktop Agent Auth (Phase 3)
- ✅ JWT refresh token endpoint
- ✅ Device pairing flow (pairing codes)
- ✅ Desktop agent `--pair CODE` flag
- ✅ API key authentication for desktop agent

### Frontend Redesign: Minecraft Pixel Theme (2026-05-18)

Full visual redesign of `Exe/desktop-app/static/` from generic Tailwind UI to a cohesive **Minecraft Pixel Theme**.

#### Files Modified

| File | Change |
|------|--------|
| `Exe/desktop-app/static/index.html` | Complete rewrite — Google Fonts (Press Start 2P + VT323), Tailwind `mc-*` color palette, dark mode, pixel overlay |
| `Exe/desktop-app/static/style.css` | Complete rewrite (153→245 lines) — All new CSS components |
| `Exe/desktop-app/static/app.js` | All HTML templates updated (15 Edit ops, 911→926 lines). JS logic unchanged. |

#### Design System

**Colors:**
| Name | Hex | Usage |
|------|-----|-------|
| Sky Blue (mc-sky) | `#5CACED` | Primary accent, progress fills, active states, info toasts |
| Cream (mc-cream) | `#FAFBD3` | Text on dark, input backgrounds, on-primary text |
| Tan/Wood (mc-wood) | `#C69F78` | Card/nav backgrounds, secondary surfaces |
| Dark Wood (mc-darkwood) | `#995A24` | Borders, toggle off, secondary buttons, dark accents |
| Grass Green (mc-grass) | `#5D6B2E` | Primary buttons, success states, Auto badge, toggles on (WCAG AA) |

**Typography:** Press Start 2P (headings) + VT323 (body) via Google Fonts

**Dark Background:** `#1a1410` with `.minecraft-bg-grid` — repeating 32px grid pattern.

#### CSS Components
- `.pixel-nav` — Wood-tone nav with dark wood bottom border
- `.pixel-card` / `.pixel-card-dark` — Pixel-bordered cards with shadow box
- `.pixel-btn` / `-primary` / `-secondary` / `-danger` — Minecraft-style pixel buttons
- `.pixel-input` — Cream inputs, dark wood border, sky blue focus
- `.pixel-toggle` — Toggle as pixel lever
- `.pixel-table` — Sharp-cornered pixel table
- `.pixel-badge` / `-green` / `-gray` — Status badges
- `.pixel-file-input` — Pixel-styled file upload
- `.status-dot` — Status indicators (synced/idle/syncing/error)
- `.text-shadow` — 2px black text shadow

### Session 2: Double Backup Fix + WCAG Text Sizes (2026-05-18)

#### Double Backup Bug Fix — `Exe/desktop-app/watcher/watcher.py`
Added `_backing_up` flag to `WorldWatcher` to prevent re-triggering during active backups:
- `_trigger` checks `not self._backing_up` before setting `backup_pending`
- `_run_backup` sets `_backing_up = True` before backup starts
- `finally` clears both flags atomically under lock

#### WCAG Text Size Compliance
**Root cause:** Press Start 2P pixel font at 7-9px illegible per WCAG 1.4.4.

| File | Change |
|------|--------|
| `style.css` | `.pixel-btn`: 10px→11px, `.pixel-badge`: 7px→13px, `.pixel-table th`: 8px→10px, file-selector: 8px→10px |
| `app.js` | All `text-[8px]`→`text-[10px]` (4), `text-[9px]`→`text-[10px]` (14), `text-[10px]`→`text-[11px]` (7) |

### Session 3: WCAG Full Compliance + App Lifecycle (2026-05-19)

#### Font Size Overhaul

| Element | Before | After |
|---------|--------|-------|
| Body text | 18px VT323 | 20px VT323 |
| Buttons (Press Start 2P) | 10-11px | 13px |
| Section headings | 11px | 14px |
| Badges | 13px VT323 | 15px VT323 |
| Table headers | 10px | 13px |
| Form labels, info text | 12px | 14px |
| Input/textareas | 16px | 18px |
| Page headings | 18px | 20px |

#### WCAG Contrast Fixes (AA/AAA)

| Issue | Before | Fix | After |
|-------|--------|-----|-------|
| Primary button (cream on green) | 3.02:1 ✗ | `#879747`→`#5D6B2E` | 5.52:1 ✓ |
| Secondary button (cream on blue) | 2.30:1 ✗ | `#5CACED`→`#2A6B99` | 5.46:1 ✓ |
| Table header | 2.24:1 ✗ | `#995A24`→`#4D3018` | 5.63:1 ✓ |
| Placeholder | 2.29:1 ✗ | `#C69F78`→`#7D6245` | 5.34:1 ✓ |
| Card secondary text | 2.24:1 ✗ | `#995A24`→`#4D3018` | 5.63:1 ✓ |
| Dark card metadata | 3.21:1 ✗ | `#995A24`→`#C69F78` | 7.20:1 ✓ |
| Toasts (success/info) | 3.02/2.30 ✗ | Darkened bg | 5.5:1 ✓ |

#### App Lifecycle — Single Instance + Auto-Shutdown

**Single-instance check** (`main.py`):
- Socket `connect_ex` port check before uvicorn starts
- If already running: calls `/api/reload` to refocus browser tab, then exits

**Tab close → kill process:**
- `beforeunload` + `sendBeacon("/api/shutdown")` → 60s cancellable countdown
- Heartbeat every 10s cancels pending shutdown (handles OAuth redirect)
- Fallback: 25s no-heartbeat timeout

**Updated files:**
| File | Change |
|------|--------|
| `Exe/desktop-app/static/style.css` | All font sizes bumped, WCAG colors |
| `Exe/desktop-app/static/app.js` | Font size classes bumped, color fixes, beforeunload + heartbeat |
| `Exe/desktop-app/static/index.html` | Tailwind mc-grass → `#5D6B2E` |
| `Exe/desktop-app/main.py` | Socket single-instance check, /api/shutdown, /api/heartbeat, /api/reload |
| `Exe/CLAUDE.md` | Created with exe-specific instructions |

---

## 🔧 Current State

### Working Features
1. ✅ Automatic backup via watchdog (world file change detection)
2. ✅ Auto-sync with local path detection
3. ✅ API key auth + device pairing for desktop agent
4. ✅ Minecraft Pixel Theme on all pages (login, dashboard, worlds, details, settings)
5. ✅ File logging, signal handling, CLI args
6. ✅ Single-instance detection (clicking exe re-opens browser)
7. ✅ Auto-shutdown on tab close (heartbeat timeout only — no beforeunload)
8. ✅ OAuth-safe shutdown (heartbeat timeout extends to 5min during OAuth flow)

---

### Session 6: OAuth Crash Fix — Server Dies on Google Sign-In (2026-05-22)

#### Root Cause
The `app.js` `beforeunload` handler called `POST /api/shutdown-now` when the browser tab navigated to Google's OAuth page. This killed the server instantly before the user could complete authentication.

**Trigger chain:**
1. User clicks "Sign in with Google" → `handleLogin()` calls `/api/auth/login`
2. `window.location.href = data.auth_url` → browser navigates to Google
3. `beforeunload` fires → `fetch("/api/shutdown-now", { keepalive: true })` → server dies
4. Google redirects back to localhost, but the server is already gone

#### Changes Made

**`Exe/desktop-app/static/app.js` — Removed `beforeunload` handler:**
- Deleted `window.addEventListener("beforeunload", ...)` that called `/api/shutdown-now`
- Tab close now relies solely on heartbeat timeout (no instant kill)

**`Exe/desktop-app/main.py` — OAuth-aware heartbeat monitor:**
- Imported `pending_auth_states` from auth router to detect active OAuth flows
- `_shutdown_pending` only honored when no OAuth states are active (`not pending_auth_states`)
- Heartbeat timeout extends from 10s → 300s while OAuth is in progress
- Once OAuth callback completes, state is popped and normal timeout resumes

#### Files Modified This Session

| File | Summary |
|------|---------|
| `Exe/desktop-app/main.py` | Imported `pending_auth_states`, OAuth-aware `_shutdown_pending` check, 300s OAuth timeout |
| `Exe/desktop-app/static/app.js` | Removed `beforeunload` shutdown handler |

#### Remaining Concern
- The compiled EXE (`dist/MinecraftBackup.exe`) has old code baked in — must rebuild with `pyinstaller build.spec` or run `python main.py` to pick up changes

---

- [ ] **Status stuck on "completed"** — Needs auto-reset in `main.py`
- [ ] **Crash recovery** — Temp zip wiped on reboot. Use `data/uploads/` (partially done)
- [ ] **ZIP_STORED for .mca** — Already compressed, skip re-compression
- [ ] **Upload delete order** — `drive.py` deletes old before new upload
- [ ] **Desktop App PyInstaller packaging** — build.spec exists, needs testing from new Exe/ location
- [ ] **Figma "Minecraft UI KIT"** — needs a Figma URL to extract textures

### Session 4: Project Restructuring (2026-05-19)

#### Directory Cleanup
- Created `Exe/.md/PRODUCTION_ROADMAP.md` — exe-only production roadmap
- Created `Exe/CLAUDE.md` — exe-specific project instructions
- Moved `design_guide.md` from root `.md/` to `Exe/.md/`
- Moved `desktop-agent/` back to root level (not part of the exe)

#### Path Fixes
- `docs/desktop-app.md`: `desktop-app/` → `Exe/desktop-app/` in tree and `cd` commands
- `docs/desktop-app-production.md`: absolute path → `Exe/desktop-app/`
- `build.spec`: `cd desktop-app` → `cd Exe/desktop-app`

---

### Session 5: Graceful Shutdown + Re-run Fix (2026-05-19)

#### Goal
Fix two UX issues:
1. App keeps running in Task Manager after closing browser tab
2. Re-running exe does nothing (browser doesn't open)

#### Changes Made

**main.py:**
| Change | Details |
|--------|---------|
| `HEARTBEAT_TIMEOUT` | 25s → 10s (faster shutdown) |
| `SHUTDOWN_DELAY` | 60s → 10s (faster countdown) |
| Second instance launch | Changed from `webbrowser.open()` to `subprocess.Popen('start "" ...', shell=True)` for reliable browser opening |
| `/api/reload` endpoint | Same subprocess fix |
| `open_browser()` function | Same subprocess fix |
| `/api/shutdown-now` endpoint | New POST endpoint for immediate shutdown (calls `stop_watcher()` then `os._exit(0)`) |

**app.js:**
| Change | Details |
|--------|---------|
| `visibilitychange` listener | Added as primary detection (more reliable than `beforeunload` per MDN) |
| `beforeunload` listener | Kept as backup |
| `renderSettings()` | Added "Shut Down App" button below Sign Out |
| `handleShutdown()` | New function calls `POST /api/shutdown-now` with confirmation dialog |

#### 🔴 UNRESOLVED: 405 Method Not Allowed

**Issue:** The `/api/heartbeat` and `/api/shutdown` endpoints return 405 errors despite being correctly defined as `@app.post()` in `main.py`.

**Evidence:**
```
POST /api/heartbeat HTTP/1.1" 405 Method Not Allowed
POST /api/shutdown HTTP/1.1" 405 Method Not Allowed
```

- Code in `main.py` clearly shows `@app.post("/api/heartbeat")` and `@app.post("/api/shutdown")`
- No conflicting routes found in any router files
- GET endpoints (like `/api/auth/me`, `/api/worlds`) work fine
- POST endpoints in routers (like `/api/auth/logout`, `/api/worlds`) work fine
- Issue persists when running directly via `python main.py` (not a PyInstaller build issue)
- FastAPI appears to be rejecting these specific POST routes for unknown reason

**Tested/verified:**
- Code syntax is correct
- No duplicate route definitions
- No middleware interference found
- Routes registered AFTER routers are included (per FastAPI order)

**Still needs investigation:**
- Why FastAPI rejects these specific POST routes while accepting POST routes in routers
- Potential FastAPI version compatibility issue
- Possible need for explicit route ordering or alternative endpoint definition

---

#### Files Modified This Session

| File | Summary |
|------|---------|
| `Exe/desktop-app/main.py` | Added shutdown endpoints, subprocess for browser, faster timeouts |
| `Exe/desktop-app/static/app.js` | Added visibilitychange, Shut Down button, handleShutdown function |

---

## 📄 Key Files

| File | Description |
|------|-------------|
| `Exe/desktop-app/static/index.html` | Frontend entry (pixel theme) |
| `Exe/desktop-app/static/style.css` | Pixel CSS (295 lines) |
| `Exe/desktop-app/static/app.js` | Vanilla JS SPA (~940 lines) |
| `Exe/desktop-app/main.py` | Desktop app entry (FastAPI + watcher) |
| `Exe/desktop-app/build.spec` | PyInstaller build config |
| `Exe/desktop-app/watcher/watcher.py` | File change watcher |
| `desktop-agent/main.py` | CLI backup agent (now at root level) |

---

## ⚠️ Important Notes

1. **Frontend is vanilla JS** in `Exe/desktop-app/static/`, NOT the React app in `frontend_Assets/`
2. `Exe/desktop-app/app/` is a separate package from `Backend/app/`
3. Run with: `cd Exe/desktop-app && python main.py` → http://127.0.0.1:8710
4. Build with: `cd Exe/desktop-app && pyinstaller build.spec`
5. DO NOT revert colors to emerald/slate file defaults
