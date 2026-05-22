# Architecture Decisions

## Auth Strategy
**Google OAuth 2.0 with PKCE** - Chosen over password auth to avoid storing credentials. PKCE verifier prevents authorization code interception. Backend stores encrypted Drive tokens for long-term API access. Desktop agent uses API key (hashed via SHA-256) instead of JWT for simplicity.

## Backup Retention
**Keep only 1 latest backup per upload.** Previous backup is deleted from Drive before uploading new one. This prevents Drive storage filling up. Background task also cleans up excess backups based on user's `max_backups_per_world` setting.

## Encryption
**Fernet (symmetric AES)** for encrypting Google OAuth credentials at rest. Key derived from `SECRET_KEY` via SHA-256. API keys stored as SHA-256 hashes (never plaintext).

## Database
**SQLite** via SQLAlchemy 2.0. Simple, zero-config. Single-user / small-team use case. Could migrate to PostgreSQL if needed (SQLAlchemy abstracts it).

## Frontend Styling
**Custom CSS (no component library).** Minecraft-inspired pixel theme using Tailwind utility classes. No shadcn/ui, no MUI. Custom components: `pixel-btn`, `pixel-card`, `pixel-input`, `pixel-toggle`.

## Rate Limiting
**slowapi** (FastAPI middleware). Conservative limits: 10/min for auth, 100/min for reads, 20/min for backups.

## CRA (Deprecated)
Currently using `react-scripts` 5.0.1 (Create React App) which is officially deprecated. 26 known npm vulnerabilities in transitive deps. Migration to Vite is planned.
