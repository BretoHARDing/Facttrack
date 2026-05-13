# Facttrack

Forensic fact tracker with a FastAPI backend and a React + TypeScript PWA frontend.

## Frontend

The frontend lives in `/frontend` and is built with Vite, React, TypeScript, React Router, Zustand, Tailwind CSS, a service worker, and IndexedDB caching.

### Run locally

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

- `VITE_API_PROXY_TARGET` defaults to `http://127.0.0.1:8000` for local FastAPI development.
- Set `VITE_API_BASE_URL` if you want the frontend to call a deployed backend directly.

### Build

```bash
cd frontend
npm run build
```

### Lint

```bash
cd frontend
npm run lint
```
