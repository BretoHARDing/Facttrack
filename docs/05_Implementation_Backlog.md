# FACTTRACK — Phase 1 Implementation Backlog

Tasks are ordered by dependency. Each slice maps to concrete files in the repository.

---

## Slice 0 — Repo Bootstrap ✅

| # | Task | Files | Status |
|---|---|---|---|
| 0.1 | Repo skeleton and directory structure | `/` | ✅ Done |
| 0.2 | `.env.example` with all required vars | `.env.example` | ✅ Done |
| 0.3 | `docker-compose.yml` (postgres, redis, api, worker, nginx, frontend) | `docker-compose.yml` | ✅ Done |
| 0.4 | Backend `Dockerfile` | `backend/Dockerfile` | ✅ Done |
| 0.5 | Frontend `Dockerfile` | `frontend/Dockerfile` | ✅ Done |
| 0.6 | `nginx/nginx.conf` | `nginx/nginx.conf` | ✅ Done |
| 0.7 | `Makefile` with common dev commands | `Makefile` | ✅ Done |
| 0.8 | `README.md` with run instructions | `README.md` | ✅ Done |
| 0.9 | `requirements.txt` pinned, CVEs patched | `backend/requirements.txt` | ✅ Done |

---

## Slice 1 — Database Schema and Migrations ✅

| # | Task | Files | Status |
|---|---|---|---|
| 1.1 | SQLAlchemy async models | `backend/app/models.py` | ✅ Done |
| 1.2 | Alembic configuration | `backend/alembic.ini`, `backend/alembic/env.py` | ✅ Done |
| 1.3 | Migration 0001: initial schema (extensions, enums, tables, indexes) | `backend/alembic/versions/0001_initial_schema.py` | ✅ Done |
| 1.4 | Migration 0002: RLS policies and role grants | `backend/alembic/versions/0002_rls_policies.py` | ✅ Done |

---

## Slice 2 — Auth and Session Model ✅

| # | Task | Files | Status |
|---|---|---|---|
| 2.1 | Auth service (bcrypt, JWT HS256, refresh tokens) | `backend/app/services/auth_service.py` | ✅ Done |
| 2.2 | TOTP MFA (pyotp, QR generation) | `backend/app/services/auth_service.py` | ✅ Done |
| 2.3 | Auth schemas (Pydantic v2) | `backend/app/schemas/auth.py` | ✅ Done |
| 2.4 | Auth routes (register, login, refresh, logout, mfa/setup, mfa/verify) | `backend/app/api/auth_routes.py` | ✅ Done |
| 2.5 | JWT dependency (`get_current_user`) | `backend/app/dependencies/auth.py` | ✅ Done |
| 2.6 | `require_role` and `require_case_access` dependencies | `backend/app/dependencies/auth.py` | ✅ Done |

---

## Slice 3 — Case Access Model ✅

| # | Task | Files | Status |
|---|---|---|---|
| 3.1 | Case and membership schemas | `backend/app/schemas/case.py` | ✅ Done |
| 3.2 | Case routes (CRUD, member management) | `backend/app/api/case_routes.py` | ✅ Done |
| 3.3 | RLS policies enforcing case membership | `backend/alembic/versions/0002_rls_policies.py` | ✅ Done |
| 3.4 | `set_rls_user()` called on every authenticated request | `backend/app/database.py` | ✅ Done |

---

## Slice 4 — CAS Storage ✅

| # | Task | Files | Status |
|---|---|---|---|
| 4.1 | CAS service (SHA-256 addressed, append-only, idempotent write) | `backend/app/services/cas_service.py` | ✅ Done |
| 4.2 | Hashing utilities | `backend/app/utils/hashing.py` | ✅ Done |

---

## Slice 5 — Evidence Ingestion Orchestrator ✅

| # | Task | Files | Status |
|---|---|---|---|
| 5.1 | Ingestion service (hash-first, CAS write, dedup, DB record, audit, enqueue) | `backend/app/services/ingestion_service.py` | ✅ Done |
| 5.2 | Evidence upload route | `backend/app/api/evidence_routes.py` | ✅ Done |

---

## Slice 6 — Parsers ✅

| # | Task | Files | Status |
|---|---|---|---|
| 6.1 | Parser base interface and `ParseResult` | `backend/app/parsers/base.py` | ✅ Done |
| 6.2 | PDF parser (PyMuPDF + Tesseract OCR fallback) | `backend/app/parsers/pdf_parser.py` | ✅ Done |
| 6.3 | Email parser (stdlib `email`, headers + body) | `backend/app/parsers/email_parser.py` | ✅ Done |
| 6.4 | Spreadsheet parser (openpyxl) | `backend/app/parsers/spreadsheet_parser.py` | ✅ Done |
| 6.5 | Plain text / CSV parser | `backend/app/parsers/text_parser.py` | ✅ Done |
| 6.6 | arq async parse worker | `backend/app/workers/parse_worker.py` | ✅ Done |

---

## Slice 7 — Evidence Retrieval / Download APIs ✅

| # | Task | Files | Status |
|---|---|---|---|
| 7.1 | Evidence list, get, download (hash-verified), artifact endpoints | `backend/app/api/evidence_routes.py` | ✅ Done |
| 7.2 | Evidence schemas | `backend/app/schemas/evidence.py` | ✅ Done |

---

## Slice 8 — Audit Logging and Verification ✅

| # | Task | Files | Status |
|---|---|---|---|
| 8.1 | Audit service (append-to-chain, prev_hash linkage, entry_hash computation) | `backend/app/services/audit_service.py` | ✅ Done |
| 8.2 | Audit chain verification (full traversal + recompute) | `backend/app/services/audit_service.py` | ✅ Done |
| 8.3 | Audit routes (list by case, verify, verify by case) | `backend/app/api/audit_routes.py` | ✅ Done |
| 8.4 | Audit schemas | `backend/app/schemas/audit.py` | ✅ Done |

---

## Slice 9 — Health and Observability ✅

| # | Task | Files | Status |
|---|---|---|---|
| 9.1 | `/health`, `/health/db`, `/health/redis` endpoints | `backend/app/api/health_routes.py` | ✅ Done |
| 9.2 | FastAPI app wiring (routers, CORS, exception handlers) | `backend/app/main.py` | ✅ Done |

---

## Slice 10 — Frontend Scaffold ✅

| # | Task | Files | Status |
|---|---|---|---|
| 10.1 | Vite + React + TypeScript project | `frontend/` | ✅ Done |
| 10.2 | API client (axios, JWT interceptor, refresh logic) | `frontend/src/api/client.ts` | ✅ Done |
| 10.3 | Auth pages (Login, Register) | `frontend/src/pages/` | ✅ Done |
| 10.4 | Case list and detail pages | `frontend/src/pages/` | ✅ Done |
| 10.5 | Evidence upload and view | `frontend/src/pages/` | ✅ Done |
| 10.6 | Audit log viewer | `frontend/src/pages/` | ✅ Done |
| 10.7 | Protected route, Layout component | `frontend/src/components/` | ✅ Done |

---

## Slice 11 — Tests (Next)

| # | Task | Files | Status |
|---|---|---|---|
| 11.1 | pytest + httpx async test setup | `backend/tests/conftest.py` | ⬜ Pending |
| 11.2 | Auth tests (register, login, MFA, refresh, invalid cases) | `backend/tests/test_auth.py` | ⬜ Pending |
| 11.3 | RLS / case isolation tests (cross-case access denied) | `backend/tests/test_rls.py` | ⬜ Pending |
| 11.4 | Evidence ingestion tests (upload, dedup, hash verification) | `backend/tests/test_ingestion.py` | ⬜ Pending |
| 11.5 | CAS integrity tests | `backend/tests/test_cas.py` | ⬜ Pending |
| 11.6 | Audit chain tests (chain validity, tamper detection) | `backend/tests/test_audit.py` | ⬜ Pending |
| 11.7 | Parser unit tests | `backend/tests/test_parsers.py` | ⬜ Pending |
| 11.8 | CI workflow | `.github/workflows/ci.yml` | ⬜ Pending |

---

## Slice 12 — Hardening (Phase 1 Completion Gate)

| # | Task | Files | Status |
|---|---|---|---|
| 12.1 | Rate limiting on auth endpoints | `backend/app/main.py` | ⬜ Pending |
| 12.2 | File size limit enforcement on upload | `backend/app/api/evidence_routes.py` | ⬜ Pending |
| 12.3 | Request logging middleware | `backend/app/main.py` | ⬜ Pending |
| 12.4 | TLS enforcement in nginx (production config) | `nginx/nginx.conf` | ⬜ Pending |
| 12.5 | Secret rotation documentation | `docs/` | ⬜ Pending |

---

## Phase 1 Completion Checklist

The system is Phase 1 complete when all of the following are true:

- [ ] User can register, login, enable MFA
- [ ] Case workspaces can be created and managed
- [ ] Case membership access is enforced at the DB layer (RLS)
- [ ] Evidence upload returns correct SHA-256
- [ ] Same file uploaded twice deduplicates within a case
- [ ] Parsed artifacts are accessible via API
- [ ] Non-members cannot access any case evidence (verified by test)
- [ ] Evidence download verifies hash before streaming
- [ ] All significant events produce audit log entries
- [ ] Audit chain verification endpoint passes
- [ ] Tampered audit entry causes verification failure
- [ ] `docker compose up` starts full stack from cold
- [ ] All Slice 11 tests pass in CI

---

## Out of Scope (Phase 2+)

- Contradiction detection engine
- Timeline intelligence
- Multimodal / RAG search
- Knowledge graph
- C2PA provenance
- ABAC beyond RBAC + case membership
- Offline-first sync
- Merkle batch sealing
- WebAuthn / FIDO2
