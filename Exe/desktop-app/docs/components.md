# Frontend Components

## Page Routes

| Route | Component | Auth | Purpose |
|-------|-----------|------|---------|
| `/` | `Login` | No | Google sign-in |
| `/auth/callback` | `AuthCallback` | No | OAuth redirect handler |
| `/dashboard` | `Dashboard` | Yes | World list, search, storage |
| `/add-world` | `AddWorld` | Yes | Create new world |
| `/worlds/:id` | `WorldDetails` | Yes | World details, upload, backups |
| `/settings` | `Settings` | Yes | Account, backup config, pairing |

## Shared Components (`src/components/`)

- **Navbar** — Top nav with logo, theme toggle, user avatar, logout
- **Sidebar** — Dashboard sidebar navigation
- **DashboardLayout** — Layout wrapper with Navbar + Sidebar + Outlet
- **WorldCard** — World summary card (name, stats, status, actions)
- **StorageWidget** — Google Drive storage usage bar
- **UploadProgress** — Sticky upload progress overlay
- **ConfirmDialog** — Modal confirmation dialog (supports danger mode)

## Contexts (`src/contexts/`)

- **AuthContext** — `user`, `loading`, `login()`, `logout()` — checks auth on mount
- **ThemeContext** — `theme`, `toggleTheme()` — dark/light with localStorage persistence

## Services (`src/services/`)

- **api** — Axios instance with base URL from `REACT_APP_API_URL`, JWT interceptor
- **driveAPI** — `worldsAPI` and `driveAPI` objects with all endpoint wrappers

## Utility

- **`cn()`** — `clsx` + `tailwind-merge` for conditional className merging

## Styling

Minecraft-inspired custom CSS via Tailwind utility classes:
- `pixel-btn` (green primary, brown secondary, red danger)
- `pixel-card` (brown with 3D border)
- `pixel-input` (dark with focus glow)
- `pixel-toggle` (green=on, red=off)
- `text-shadow` for pixel heading effect
- `minecraft-bg-grid` for dotted grid background
