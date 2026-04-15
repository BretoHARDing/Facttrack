# FACTTRACK

A Phase 1 forensic evidence platform that guarantees immutable evidence handling, strict case isolation, secure authenticated access, MIME-routed ingestion and parsing, and a tamper-evident audit trail.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI + SQLAlchemy 2.0 async |
| Database | PostgreSQL 16 (pgvector, pgcrypto) |
| Cache / Queue | Redis 7 + arq |
| Auth | JWT (HS256) + refresh tokens + TOTP MFA |
| Storage | SHA-256 content-addressed local CAS |
| Parsing | PyMuPDF, pytesseract, openpyxl, stdlib email |
| Frontend | React 18 + TypeScript + Vite |
| Reverse proxy | Nginx |
| Dev infra | Docker Compose |

---

## Quick start

### Prerequisites

- Docker ≥ 24 and Docker Compose v2
- `make` (optional but recommended)

### 1. Clone and configure

```bash
git clone https://github.com/BretoHARDing/Facttrack.git
cd Facttrack
cp .env.example .env
# Edit .env — change POSTGRES_PASSWORD and SECRET_KEY before use
```

### 2. Start the stack

```bash
make up-build   # builds images + starts all services
# or without make:
docker compose up -d --build
```

The first start automatically runs Alembic migrations.

### 3. Access the app

| Service | URL |
|---|---|
| Frontend (via nginx) | http://localhost |
| Backend API | http://localhost/api/v1 |
| API docs (Swagger) | http://localhost/api/v1/docs |
| Health check | http://localhost/api/v1/health |

---

## Common commands

```bash
make up              # start services (no rebuild)
make down            # stop services
make logs            # tail all logs
make logs-api        # tail API logs
make shell-api       # bash shell inside api container
make shell-db        # psql shell
make migrate         # run pending migrations
make migrate-down    # rollback last migration
make test            # run backend tests
make lint            # lint with ruff
make ps              # show container status
```

---

## Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set env vars
export DATABASE_URL="postgresql+asyncpg://facttrack:facttrack_secret@localhost:5432/facttrack"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="dev_secret_key_replace_in_prod"

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8000

# Start worker (separate terminal)
python -m arq app.workers.parse_worker.WorkerSettings
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # starts Vite dev server on http://localhost:5173
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

---

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers
│   │   ├── services/     # Business logic
│   │   ├── parsers/      # MIME-routed evidence parsers
│   │   ├── workers/      # Async parse worker (arq)
│   │   ├── schemas/      # Pydantic v2 request/response schemas
│   │   ├── dependencies/ # FastAPI dependency injectors
│   │   ├── utils/        # Hashing utilities
│   │   ├── config.py     # Settings (pydantic-settings)
│   │   ├── database.py   # Async SQLAlchemy engine + RLS helper
│   │   ├── models.py     # SQLAlchemy ORM models
│   │   └── main.py       # FastAPI app factory
│   ├── alembic/          # Database migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios client + typed API functions
│   │   ├── components/   # Layout, ProtectedRoute
│   │   ├── context/      # AuthContext
│   │   ├── pages/        # Login, Register, Cases, Evidence, Audit
│   │   └── types/        # TypeScript domain types
│   ├── Dockerfile
│   └── package.json
├── nginx/
│   └── nginx.conf
├── docs/
│   ├── 01_PRD_Phase1.md
│   ├── 02_Architecture_Phase1.md
│   ├── 03_Data_Model.md
│   ├── 04_API_Surface.md
│   └── 05_Implementation_Backlog.md
├── docker-compose.yml
├── .env.example
└── Makefile
```

---

## Security notes

- Change `POSTGRES_PASSWORD` and `SECRET_KEY` before deploying anywhere.
- MFA (TOTP) is available via `POST /api/v1/auth/mfa/setup` after login.
- PostgreSQL row-level security is enabled on all evidence and audit tables.
- The CAS directory (`/data/cas`) is append-only — originals are never modified.
- Audit log entries form a hash chain; verify integrity via `GET /api/v1/audit/verify`.

---

## Documentation

Full specifications are in [`docs/`](docs/):

- [PRD](docs/01_PRD_Phase1.md)
- [Architecture](docs/02_Architecture_Phase1.md)
- [Data model](docs/03_Data_Model.md)
- [API surface](docs/04_API_Surface.md)
- [Implementation backlog](docs/05_Implementation_Backlog.md)
