# FACTTRACK — Phase 1 Architecture Specification

## 1. System Overview

FACTTRACK Phase 1 is a monolithic-first REST API backend with a thin React frontend. The architecture is designed for correctness and auditability rather than premature scale. All components run in Docker containers orchestrated by Docker Compose.

```
┌─────────────────────────────────────────────────────────┐
│                        Client                           │
│             React SPA (served by Nginx)                 │
└────────────────────────┬────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────┐
│                   API Server (Node.js)                  │
│   Auth │ Cases │ Evidence │ Audit │ Search │ Parsers     │
└──┬──────────┬──────────┬──────────┬────────────────┬────┘
   │          │          │          │                │
   ▼          ▼          ▼          ▼                ▼
 PostgreSQL  Redis     Local CAS  Worker Queue    Tesseract
 (primary    (cache,   (SHA-256   (BullMQ/Redis)  (OCR sidecar)
  store +    sessions, addressed
  RLS)       queues)   filesystem)
```

---

## 2. Component Inventory

| Component | Technology | Role |
|---|---|---|
| API Server | Node.js (Fastify) | HTTP request handling, auth, business logic |
| Worker | Node.js (same codebase, worker entry) | Async evidence parsing, audit sealing |
| PostgreSQL | PostgreSQL 16 | Primary structured store; RLS enforced |
| Redis | Redis 7 | Session tokens, job queues (BullMQ), rate-limit counters |
| CAS | Local filesystem (Docker volume) | Immutable content-addressed file storage |
| Nginx | Nginx | Reverse proxy, TLS termination, SPA serving |
| OCR Sidecar | Tesseract via child process | PDF OCR fallback |
| Frontend | React + TypeScript (Vite) | Browser UI |

---

## 3. Data Flow: Upload to Audit

```
Client
  │
  │  POST /api/v1/cases/:caseId/evidence  (multipart/form-data)
  ▼
API Server
  ├─ 1. Authenticate JWT; verify case membership
  ├─ 2. Read raw bytes from stream
  ├─ 3. Compute SHA-256 of raw bytes  ← hash-first
  ├─ 4. Check CAS: if hash exists, skip write (deduplication)
  ├─ 5. Write bytes to CAS at path /<prefix2>/<hash>
  ├─ 6. Insert evidence record (status: PENDING) in PostgreSQL
  ├─ 7. Emit audit event: EVIDENCE_UPLOADED
  ├─ 8. Enqueue parse job → Redis/BullMQ
  └─ 9. Return 202 Accepted { evidenceId, sha256, status: "PENDING" }

Worker (async)
  ├─ 1. Dequeue parse job
  ├─ 2. Read file from CAS by hash
  ├─ 3. Detect MIME type
  ├─ 4. Route to appropriate parser
  ├─ 5. Parser extracts text/metadata; stores derived artifact in DB
  ├─ 6. Update evidence record status: PARSED or PARSE_FAILED
  └─ 7. Emit audit event: EVIDENCE_PARSED

Client polls GET /api/v1/cases/:caseId/evidence/:id for status
```

---

## 4. Trust Boundaries

```
Internet
  │
  └─[TLS]─▶ Nginx (DMZ)
               │
               └─[Internal network]─▶ API Server
                                          │
                                  ┌───────┴────────┐
                                  │                │
                            PostgreSQL           Redis
                            (no direct           (no direct
                             external             external
                             access)              access)
                                  │
                                CAS volume
                            (no direct
                             external
                             access)
```

- PostgreSQL, Redis, and CAS are on an internal Docker network not exposed to the host or internet.
- The API server is the sole entry point for application logic.
- RLS in PostgreSQL is a second-layer enforcement independent of application logic.

---

## 5. Storage Model

### 5.1 Content-Addressed Storage (CAS)

Files are stored at:
```
{CAS_ROOT}/{hash[0:2]}/{hash[2:4]}/{hash}
```

Example:
```
/data/cas/ab/cd/abcdef1234567890...
```

Properties:
- **Append-only**: no delete API; no overwrite.
- **Deduplication**: identical files share one CAS entry; evidence records reference the hash.
- **MIME-agnostic**: the CAS stores raw bytes only; MIME type is stored in the evidence DB record.
- **Future**: CAS interface (`CASAdapter`) will be implemented such that a LocalCASAdapter can be swapped for an S3CASAdapter without changing business logic.

### 5.2 PostgreSQL

See `03_Data_Model.md` for the full schema. Key points:
- All tables use UUIDs as primary keys.
- Evidence table stores `sha256_hash`, `mime_type`, `file_size`, `original_filename`, `status`, `case_id`, `uploaded_by`.
- RLS policies on `evidence`, `audit_log`, `case_memberships`, and `derived_artifacts` tables enforce case isolation at the DB layer.

### 5.3 Derived Artifacts

Parsed text and metadata are stored in a `derived_artifacts` table referencing the parent evidence row. The CAS may also store derived files (e.g., extracted PDF text as a `.txt` file) addressed by their own SHA-256.

---

## 6. Authentication and Session Model

```
Registration → bcrypt(password) → user record
Login        → verify password + TOTP → issue access_token (JWT, 15min) + refresh_token (opaque, 7d)
Request      → Bearer access_token in Authorization header
Refresh      → POST /auth/refresh with refresh_token cookie → new token pair; old refresh revoked
Logout       → revoke refresh_token in DB; remove from Redis
```

### JWT Claims

```json
{
  "sub": "<userId>",
  "email": "<email>",
  "platform_role": "case_owner | case_investigator | case_reviewer | platform_admin",
  "iat": 1234567890,
  "exp": 1234568790,
  "jti": "<tokenId>"
}
```

- Access tokens are stateless and verified via RS256 public key.
- Refresh tokens are stored hashed in PostgreSQL; each use rotates the token.
- Redis stores a short-lived access token denylist for immediate revocation between refresh cycles.

---

## 7. Row-Level Security Strategy

All evidence-related tables have RLS enabled. The key policies:

### `cases` table
```sql
-- Users can only see cases they are members of
CREATE POLICY case_member_select ON cases
  FOR SELECT USING (
    id IN (
      SELECT case_id FROM case_memberships WHERE user_id = current_setting('app.current_user_id')::uuid
    )
  );
```

### `evidence` table
```sql
CREATE POLICY evidence_case_member ON evidence
  FOR ALL USING (
    case_id IN (
      SELECT case_id FROM case_memberships WHERE user_id = current_setting('app.current_user_id')::uuid
    )
  );
```

The API server sets `app.current_user_id` at the start of each transaction using the authenticated JWT's `sub` claim. This makes RLS enforcement automatic for all queries in that transaction, regardless of which ORM query runs.

---

## 8. Parser Routing

```
Inbound MIME type
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │              ParserRouter                   │
  ├─────────────────────────────────────────────┤
  │  application/pdf              → PDFParser   │
  │  message/rfc822               → EmailParser │
  │  application/vnd.ms-excel     → XLSParser   │
  │  application/vnd.openxml...   → XLSXParser  │
  │  text/plain | text/csv        → TextParser  │
  │  */*  (fallback)              → RawStore    │
  └─────────────────────────────────────────────┘
```

Each parser implements a common interface:
```typescript
interface Parser {
  canHandle(mimeType: string): boolean;
  parse(input: ParseInput): Promise<ParseResult>;
}

interface ParseResult {
  text: string | null;
  metadata: Record<string, unknown>;
  derivedArtifacts: DerivedArtifact[];
  parseWarnings: string[];
}
```

The `PDFParser` attempts native text extraction first; if the extracted text is below a confidence threshold (e.g., fewer than 50 characters per page on average), it falls back to Tesseract OCR.

---

## 9. Audit Chain Design

Every significant event is written to `audit_log` with the following structure:

```
entry_id   | UUID, PK
prev_hash  | SHA-256 of the previous entry's canonical representation
event_type | Enum (see event catalog)
actor_id   | UUID (user who triggered the event; null for system events)
case_id    | UUID (nullable; null for auth events)
subject_id | UUID (nullable; ID of the evidence, user, etc. affected)
payload    | JSONB (event-specific data)
created_at | TIMESTAMPTZ, set by DB
entry_hash | SHA-256(entry_id || prev_hash || event_type || actor_id || payload || created_at)
```

The `entry_hash` is computed by the application before insert and verified on read. The `prev_hash` of the first entry is a fixed sentinel (`0000...0`). Chain verification traverses entries in `created_at` order, recomputing each `entry_hash` and confirming that `prev_hash` equals the prior entry's `entry_hash`.

### Event Catalog (Phase 1)

| Event Type | Trigger |
|---|---|
| `USER_REGISTERED` | New user created |
| `USER_LOGIN` | Successful login |
| `USER_LOGIN_FAILED` | Failed login attempt |
| `USER_MFA_ENABLED` | MFA activated |
| `USER_LOGOUT` | Explicit logout |
| `CASE_CREATED` | New case workspace |
| `CASE_UPDATED` | Case metadata changed |
| `CASE_ARCHIVED` | Case archived |
| `MEMBER_ADDED` | User added to case |
| `MEMBER_REMOVED` | User removed from case |
| `MEMBER_ROLE_CHANGED` | Member's case role changed |
| `EVIDENCE_UPLOADED` | File upload accepted |
| `EVIDENCE_PARSED` | Parsing completed |
| `EVIDENCE_PARSE_FAILED` | Parsing failed |
| `EVIDENCE_VIEWED` | Evidence record accessed |
| `EVIDENCE_DOWNLOADED` | Original file downloaded |
| `EVIDENCE_EXPORTED` | Evidence exported |
| `AUDIT_VERIFIED` | Audit chain verification run |

---

## 10. Optional Merkle Sealing Path (Deferred)

Architecture is designed to accommodate Merkle batch sealing without schema changes. A future `merkle_seals` table would:
- Collect the `entry_hash` values of all audit entries since the last seal.
- Construct a Merkle tree over those hashes.
- Store the Merkle root, the timestamp, and an optional external signature.
- Reference back to the sealed entry range.

This is not implemented in Phase 1 but is a documented extension point.

---

## 11. Deployment Topology (Phase 1 — Local)

```yaml
services:
  nginx:        # port 443/80 → api:3000, frontend:80
  api:          # Node.js API server
  worker:       # Node.js async worker (same image, different CMD)
  postgres:     # PostgreSQL 16 with init scripts
  redis:        # Redis 7
  frontend:     # Nginx serving React build
volumes:
  postgres_data:
  redis_data:
  cas_data:     # Content-addressed storage root
```

All services share an internal `facttrack_net` bridge network. Only Nginx exposes external ports.
