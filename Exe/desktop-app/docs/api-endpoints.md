# API Endpoints

Base URL: `http://localhost:8000`

## Auth (`/api/auth`)

| Method | Path | Auth | Rate | Description |
|--------|------|------|------|-------------|
| GET | `/google/login` | No | 10/min | Returns Google OAuth URL (PKCE) |
| GET | `/google/callback` | No | 10/min | OAuth callback, redirects to frontend with JWT |
| GET | `/me` | JWT | 10/min | Current user profile info |
| POST | `/logout` | JWT | 10/min | Logout (client-side only, no token invalidation) |
| POST | `/refresh` | No | 10/min | Exchange refresh token for new JWT |

## Worlds (`/api/worlds`)

| Method | Path | Auth | Rate | Description |
|--------|------|------|------|-------------|
| GET | `` | JWT | 100/min | List all worlds for user |
| POST | `` | JWT | 100/min | Create world (name, description, local_path) |
| GET | `/{id}` | JWT | 100/min | Get world details |
| PUT | `/{id}` | JWT | 100/min | Update world (partial) |
| DELETE | `/{id}` | JWT | 100/min | Delete world (DB only, not Drive backups) |

## Drive Backups (`/api/drive`)

| Method | Path | Auth | Rate | Description |
|--------|------|------|------|-------------|
| POST | `/worlds/{id}/backup` | JWT | 20/min | Upload ZIP backup to Drive |
| GET | `/worlds/{id}/backups` | JWT | 100/min | List backups for world |
| GET | `/worlds/{id}/backups/{bid}/download-link` | JWT | 100/min | Get Drive download link |
| DELETE | `/worlds/{id}/backups/{bid}` | JWT | 100/min | Delete backup from Drive + DB |
| GET | `/storage` | JWT | 100/min | Google Drive storage quota |

## Pairing (`/api/auth/pair`)

| Method | Path | Auth | Rate | Description |
|--------|------|------|------|-------------|
| POST | `` | JWT | 10/min | Generate 6-char pairing code (5min expiry) |
| POST | `/exchange` | No | 10/min | Exchange code for permanent API key |
| GET | `/status` | JWT | 10/min | Check if user has API key paired |

## Health

| Method | Path | Auth | Rate | Description |
|--------|------|------|------|-------------|
| GET | `/` | No | - | API info |
| GET | `/health` | No | - | Basic health |
| GET | `/health/live` | No | - | Liveness probe |
| GET | `/health/ready` | No | - | Readiness + DB check |

## Auth Methods

1. **JWT Bearer token** (Authorization header) — for web frontend
