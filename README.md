# Facttrack

Forensic fact tracker with a FastAPI backend and a React + TypeScript PWA frontend.

## Build surface

Facttrack ships as two build deliverables:

- **Backend:** `app/` as a FastAPI application served with Uvicorn.
- **Frontend:** `frontend/` as a Vite production bundle emitted to `frontend/dist/`.

The repository now exposes one top-level orchestration layer for install, run, lint, build, validation, and packaging:

```bash
make help
```

## Environment configuration

### Backend

Copy `.env.example` to `.env` and adjust values for your environment.

Key backend settings:

- `DATABASE_URL`: async PostgreSQL connection string used by SQLAlchemy.
- `JWT_SECRET` and `JWT_REFRESH_SECRET`: required application secrets.
- `CAS_BACKEND`, `CAS_LOCAL_DIR`, `CAS_S3_BUCKET`, `CAS_S3_PREFIX`: content-addressed storage configuration.
- `CORS_ORIGINS`: JSON array of allowed frontend origins.
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`: optional matrix-extraction settings.

### Frontend

Copy `frontend/.env.example` to `frontend/.env`.

- **Development:** leave `VITE_API_BASE_URL` empty and set `VITE_API_PROXY_TARGET` to the backend origin.
- **Production build:** use `frontend/.env.production.example` and set `VITE_API_BASE_URL` to the deployed API origin. `VITE_API_PROXY_TARGET` is only used by the Vite dev server.

## Local development happy path

1. **Install dependencies**

   ```bash
   cd <repo-root>
   make install
   ```

2. **Create environment files**

   ```bash
   cp .env.example .env
   cp frontend/.env.example frontend/.env
   ```

3. **Start PostgreSQL**

   Facttrack expects a PostgreSQL database that matches `DATABASE_URL`. For local development the default connection string targets:

   ```text
   postgresql+asyncpg://facttrack:facttrack@127.0.0.1:5432/facttrack
   ```

4. **Create database tables**

   ```bash
   cd <repo-root>
   make init-db
   ```

5. **Run the backend in one terminal**

   ```bash
   cd <repo-root>
   make dev-backend
   ```

6. **Run the frontend in a second terminal**

   ```bash
   cd <repo-root>
   make dev-frontend
   ```

The backend will be available at `http://127.0.0.1:8000` and the frontend at `http://127.0.0.1:5173`.

## Validation

### Backend validation

The repository now exposes backend validation through:

```bash
cd <repo-root>
make backend-validate
```

That target performs:

- Python bytecode compilation for `app/`, `ingestion/`, and `scripts/`
- A FastAPI smoke test against `GET /health`

### Frontend validation

```bash
cd <repo-root>
make frontend-lint
make frontend-build
```

### Full repository validation

```bash
cd <repo-root>
make validate
```

## Build outputs

### Backend artifact

```bash
cd <repo-root>
make package-backend
```

This produces `dist/facttrack-backend-src.tar.gz`, a source deployment bundle containing the FastAPI app, ingestion helpers, runtime requirements, and documentation needed to deploy the backend.

### Frontend artifact

```bash
cd <repo-root>
make frontend-build
```

This produces static assets in `frontend/dist/`.

## Deployment notes

- Serve the backend with `uvicorn app.main:app`.
- Serve `frontend/dist/` from a static web server or CDN.
- Point `VITE_API_BASE_URL` at the deployed backend so the frontend can reach `/api/v1/auth`, `/api/v1/cases`, `/api/v1/evidence/upload`, and `/api/v1/ai/extract-matrix`.
- Backend and frontend can be deployed separately as long as `CORS_ORIGINS` and `VITE_API_BASE_URL` agree on the public origins.

## Integration assumptions

The frontend is built around these backend routes:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/cases/`
- `POST /api/v1/evidence/upload`
- `POST /api/v1/ai/extract-matrix`

Offline behavior is limited to cached NSW Evidence Matrix results stored in IndexedDB. New uploads, case creation, authentication, and fresh matrix extraction still require backend connectivity.

## CI

GitHub Actions now enforces the same contract remotely through `.github/workflows/build.yml`:

- backend dependency install and `make backend-validate`
- frontend dependency install and `make frontend-lint`
- frontend production build with `make frontend-build`

## Troubleshooting

- **`make backend-validate` fails during import:** verify that `.env` exists and that required Python dependencies are installed.
- **Database connection errors:** start PostgreSQL and confirm `DATABASE_URL` matches a reachable database.
- **Frontend API requests fail in development:** confirm `frontend/.env` keeps `VITE_API_BASE_URL` empty and that `VITE_API_PROXY_TARGET` matches the backend origin.
- **Production frontend cannot reach the API:** rebuild the frontend with `VITE_API_BASE_URL` set to the deployed backend URL.
