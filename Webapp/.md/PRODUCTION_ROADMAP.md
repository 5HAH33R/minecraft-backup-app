# Minecraft Backup Web App — Production Roadmap

This file contains all remaining tasks to make the web app (Backend + React frontend) production-ready.

---

## Current State

### ✅ Completed Features
- Google OAuth authentication (PKCE)
- World CRUD operations
- Manual backup upload to Google Drive
- API key authentication for desktop agent (hashed)
- Rate limiting (slowapi)
- Health endpoints (/health, /health/live, /health/ready)
- Retry logic for Google Drive operations (tenacity)
- Dark mode support (frontend)
- Structured logging (basic)

### 📁 Project Structure
```
minecraft-backup-app/
├── Backend/app/           (FastAPI)
│   ├── routers/           (auth, worlds, drive, api_keys, pairing, refresh)
│   ├── services/          (google_drive_service)
│   ├── schemas/           (world.py Pydantic models)
│   └── models/            (User, World, Backup, PairingCode)
├── frontend/src/          (React)
│   ├── pages/             (dashboard, login, AddWorld, WorldDetails, Settings)
│   ├── components/        (Navbar, WorldCard, StorageWidget, etc.)
│   └── contexts/          (AuthContext, ThemeContext)
└── Exe/                   (Desktop app + agent — separate roadmap)
```

---

## Remaining Tasks

### Phase 1: Database & Infrastructure (High Priority)

#### 1.1 PostgreSQL Migration
- [ ] Install psycopg2-binary: `pip install psycopg2-binary`
- [ ] Update `config.py` DATABASE_URL for PostgreSQL
- [ ] Update `database.py` — remove SQLite-specific args
- [ ] Create PostgreSQL database
- [ ] Update requirements.txt

#### 1.2 Database Migrations (Alembic)
- [ ] Install Alembic: `pip install alembic`
- [ ] Initialize: `cd Backend && alembic init migrations`
- [ ] Configure alembic.ini for PostgreSQL
- [ ] Generate initial migration
- [ ] Remove `Base.metadata.create_all()` from main.py
- [ ] Document migration process

### Phase 2: Security Hardening (High Priority)

#### 2.1 Enhanced Secrets
- [ ] Add SECRET_KEY validation (minimum 32 chars)
- [ ] Implement JWT refresh token rotation
- [ ] Add security headers middleware

#### 2.2 Input Validation
- [ ] Add path traversal protection for file operations
- [ ] Add filename sanitization for uploads

#### 2.3 CORS Configuration
- [ ] Update `config.py` ALLOWED_ORIGINS for production domains
- [ ] Add TrustedHostMiddleware

### Phase 3: Frontend Enhancements (Medium Priority)

#### 3.1 UX Improvements
- [ ] Add loading skeletons (dashboard, world details)
- [ ] Add responsive design (mobile-friendly)
- [ ] Add Error Boundary component

#### 3.2 API Consolidation
- [ ] Merge driveAPI.js into api.js (single service)
- [ ] Add request/response interceptors

### Phase 4: Infrastructure & Deployment (High Priority)

#### 4.1 Docker
- [ ] Create Backend/Dockerfile
- [ ] Create frontend/Dockerfile (multi-stage build)
- [ ] Create docker-compose.yml

#### 4.2 CI/CD
- [ ] Create .github/workflows/ci.yml
- [ ] Add test runner on PR
- [ ] Add Docker build on push to main

#### 4.3 Optional: Kubernetes
- [ ] Create k8s/ directory with deployment configs
- [ ] Add ingress configuration

### Phase 5: Monitoring & Observability (Medium Priority)

#### 5.1 Error Tracking
- [ ] Install Sentry: `pip install sentry-sdk[fastapi]`
- [ ] Add Sentry initialization to main.py

#### 5.2 Metrics
- [ ] Add Prometheus: `pip install prometheus-fastapi-instrumentator`
- [ ] Expose /metrics endpoint

#### 5.3 Logging Enhancement
- [ ] Install structlog: `pip install structlog`
- [ ] Create app/logging.py with structured logging
- [ ] Add request ID middleware

### Phase 6: Testing (Medium Priority)

#### 6.1 Backend Tests
- [ ] Install pytest: `pip install pytest pytest-asyncio`
- [ ] Create tests/test_routers/
- [ ] Create tests/test_services/
- [ ] Add database fixtures

#### 6.2 Frontend Tests
- [ ] Install Jest + React Testing Library
- [ ] Create component tests
- [ ] Add API mock tests

#### 6.3 Load Testing
- [ ] Create k6 load test scenarios
- [ ] Test concurrent uploads
- [ ] Test rate limiting

---

## Implementation Order

### Week 1-2: Foundation
1. PostgreSQL migration
2. Alembic migrations
3. Security headers & CORS
4. Docker setup

### Week 3: Reliability
5. Sentry error tracking
6. Structured logging
7. Prometheus metrics
8. CI/CD pipeline

### Week 4-5: Frontend
9. Loading skeletons
10. Error boundaries
11. Responsive design
12. API consolidation

### Week 6: Testing
13. Backend unit tests
14. Frontend tests
15. Load testing
16. Documentation

---

## Files to Modify

### Backend
| File | Changes |
|------|---------|
| `config.py` | PostgreSQL URL, ALLOWED_ORIGINS validation |
| `database.py` | Remove SQLite args |
| `main.py` | Alembic, Sentry, structlog, Prometheus |
| `dependencies.py` | Enhanced security |
| `requirements.txt` | Add packages |

### Frontend
| File | Changes |
|------|---------|
| `src/services/api.js` | Merge driveAPI.js |
| `src/pages/*.js` | Loading states |
| `src/App.js` | Error boundary |
| `package.json` | Add test libs |

---

## Notes

- All changes must be tested before committing
- Use feature flags for gradual rollout
- Document all environment variables
- Maintain backward compatibility where possible
