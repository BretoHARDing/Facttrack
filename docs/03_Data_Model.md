# FACTTRACK — Domain and Data Model

## 1. Entity Overview

```
users
  ├── case_memberships ──► cases
  │                          ├── evidence
  │                          │     ├── derived_artifacts
  │                          │     └── parse_results
  │                          └── audit_log
  └── refresh_tokens
```

---

## 2. Table Definitions

### 2.1 `users`

```sql
CREATE TABLE users (
  id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  email             TEXT        NOT NULL UNIQUE,
  password_hash     TEXT        NOT NULL,
  platform_role     TEXT        NOT NULL DEFAULT 'case_investigator'
                                CHECK (platform_role IN ('platform_admin','case_owner','case_investigator','case_reviewer')),
  totp_secret       TEXT,                        -- NULL until MFA enrolled
  totp_enabled      BOOLEAN     NOT NULL DEFAULT false,
  is_active         BOOLEAN     NOT NULL DEFAULT true,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

**Chain-of-custody fields**: `created_at`, `updated_at`, `is_active` (soft delete only).

---

### 2.2 `refresh_tokens`

```sql
CREATE TABLE refresh_tokens (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash    TEXT        NOT NULL UNIQUE,   -- bcrypt or SHA-256 of the opaque token
  expires_at    TIMESTAMPTZ NOT NULL,
  revoked_at    TIMESTAMPTZ,                   -- NULL = still valid
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON refresh_tokens (user_id);
CREATE INDEX ON refresh_tokens (token_hash);
```

---

### 2.3 `cases`

```sql
CREATE TABLE cases (
  id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT        NOT NULL,
  description   TEXT,
  status        TEXT        NOT NULL DEFAULT 'active'
                            CHECK (status IN ('active','archived')),
  created_by    UUID        NOT NULL REFERENCES users(id),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  archived_at   TIMESTAMPTZ
);
```

---

### 2.4 `case_memberships`

```sql
CREATE TABLE case_memberships (
  id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id     UUID        NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
  user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  case_role   TEXT        NOT NULL DEFAULT 'case_investigator'
              CHECK (case_role IN ('case_owner','case_investigator','case_reviewer')),
  added_by    UUID        REFERENCES users(id),
  added_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  removed_at  TIMESTAMPTZ,                     -- NULL = active membership
  UNIQUE (case_id, user_id)
);
CREATE INDEX ON case_memberships (user_id);
CREATE INDEX ON case_memberships (case_id);
```

---

### 2.5 `evidence`

```sql
CREATE TYPE evidence_status AS ENUM (
  'PENDING',
  'PARSING',
  'PARSED',
  'PARSE_FAILED',
  'UNSUPPORTED'
);

CREATE TABLE evidence (
  id                UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
  case_id           UUID            NOT NULL REFERENCES cases(id) ON DELETE RESTRICT,
  uploaded_by       UUID            NOT NULL REFERENCES users(id),
  original_filename TEXT            NOT NULL,
  mime_type         TEXT            NOT NULL,
  file_size         BIGINT          NOT NULL,
  sha256_hash       TEXT            NOT NULL,       -- hex-encoded SHA-256 of original bytes
  cas_path          TEXT            NOT NULL,       -- relative path inside CAS root
  status            evidence_status NOT NULL DEFAULT 'PENDING',
  parse_error       TEXT,
  uploaded_at       TIMESTAMPTZ     NOT NULL DEFAULT now(),
  parsed_at         TIMESTAMPTZ,
  description       TEXT,
  tags              TEXT[]          DEFAULT '{}',
  UNIQUE (case_id, sha256_hash)                     -- deduplication per case
);
CREATE INDEX ON evidence (case_id);
CREATE INDEX ON evidence (sha256_hash);
CREATE INDEX ON evidence (uploaded_by);
```

**Chain-of-custody fields**: `uploaded_by`, `uploaded_at`, `sha256_hash`, `cas_path`, `status`.

---

### 2.6 `derived_artifacts`

```sql
CREATE TYPE artifact_type AS ENUM (
  'EXTRACTED_TEXT',
  'OCR_TEXT',
  'EMAIL_HEADERS',
  'EMAIL_BODY',
  'EMAIL_ATTACHMENT_LIST',
  'SPREADSHEET_TEXT',
  'SPREADSHEET_STRUCTURE',
  'RAW_METADATA'
);

CREATE TABLE derived_artifacts (
  id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
  evidence_id     UUID          NOT NULL REFERENCES evidence(id) ON DELETE CASCADE,
  artifact_type   artifact_type NOT NULL,
  content         TEXT,                         -- extracted text (nullable for binary artifacts)
  cas_path        TEXT,                         -- if artifact is stored in CAS (nullable)
  sha256_hash     TEXT,                         -- hash of artifact content or file
  metadata        JSONB         NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX ON derived_artifacts (evidence_id);
CREATE INDEX ON derived_artifacts (artifact_type);
```

---

### 2.7 `audit_log`

```sql
CREATE TYPE audit_event_type AS ENUM (
  'USER_REGISTERED',
  'USER_LOGIN',
  'USER_LOGIN_FAILED',
  'USER_MFA_ENABLED',
  'USER_LOGOUT',
  'CASE_CREATED',
  'CASE_UPDATED',
  'CASE_ARCHIVED',
  'MEMBER_ADDED',
  'MEMBER_REMOVED',
  'MEMBER_ROLE_CHANGED',
  'EVIDENCE_UPLOADED',
  'EVIDENCE_PARSED',
  'EVIDENCE_PARSE_FAILED',
  'EVIDENCE_VIEWED',
  'EVIDENCE_DOWNLOADED',
  'EVIDENCE_EXPORTED',
  'AUDIT_VERIFIED'
);

CREATE TABLE audit_log (
  id          UUID             PRIMARY KEY DEFAULT gen_random_uuid(),
  prev_hash   TEXT             NOT NULL,     -- SHA-256 of prior entry; sentinel '0000...0' for first
  event_type  audit_event_type NOT NULL,
  actor_id    UUID             REFERENCES users(id),
  case_id     UUID             REFERENCES cases(id),
  subject_id  UUID,                          -- ID of the entity acted upon
  payload     JSONB            NOT NULL DEFAULT '{}',
  created_at  TIMESTAMPTZ      NOT NULL DEFAULT now(),
  entry_hash  TEXT             NOT NULL      -- SHA-256(id||prev_hash||event_type||actor_id||payload||created_at)
);
CREATE INDEX ON audit_log (case_id);
CREATE INDEX ON audit_log (actor_id);
CREATE INDEX ON audit_log (created_at);
-- No DELETE or UPDATE permissions granted on this table to the application role
```

**Chain integrity**: `prev_hash` links to `entry_hash` of the chronologically prior record. `entry_hash` is computed by the application layer before insert. No triggers or DB-computed columns are used so that the hash computation is explicit and testable in application code.

---

## 3. Row-Level Security Policies

RLS is enabled on all tables that contain case-scoped data.

```sql
-- Enable RLS
ALTER TABLE cases             ENABLE ROW LEVEL SECURITY;
ALTER TABLE case_memberships  ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence          ENABLE ROW LEVEL SECURITY;
ALTER TABLE derived_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log         ENABLE ROW LEVEL SECURITY;

-- The application sets this at the start of each transaction:
-- SET LOCAL app.current_user_id = '<uuid>';

-- cases: visible only to members
CREATE POLICY case_select ON cases FOR SELECT
  USING (id IN (
    SELECT case_id FROM case_memberships
    WHERE user_id = current_setting('app.current_user_id')::uuid
      AND removed_at IS NULL
  ));

-- case_memberships: visible only to members of the same case
CREATE POLICY membership_select ON case_memberships FOR SELECT
  USING (case_id IN (
    SELECT case_id FROM case_memberships
    WHERE user_id = current_setting('app.current_user_id')::uuid
      AND removed_at IS NULL
  ));

-- evidence: accessible only to case members
CREATE POLICY evidence_select ON evidence FOR ALL
  USING (case_id IN (
    SELECT case_id FROM case_memberships
    WHERE user_id = current_setting('app.current_user_id')::uuid
      AND removed_at IS NULL
  ));

-- derived_artifacts: accessible only if parent evidence is accessible
CREATE POLICY artifact_select ON derived_artifacts FOR ALL
  USING (evidence_id IN (
    SELECT id FROM evidence
  ));

-- audit_log: accessible only to case members (case_id-scoped entries)
CREATE POLICY audit_select ON audit_log FOR SELECT
  USING (
    case_id IS NULL  -- system/auth events: restrict to platform_admin via app layer
    OR case_id IN (
      SELECT case_id FROM case_memberships
      WHERE user_id = current_setting('app.current_user_id')::uuid
        AND removed_at IS NULL
    )
  );
```

The application database role (`facttrack_app`) is granted `SELECT, INSERT, UPDATE` on standard tables and only `SELECT, INSERT` on `audit_log` (no UPDATE, no DELETE).

---

## 4. Role and Permission Matrix

| Action | `platform_admin` | `case_owner` | `case_investigator` | `case_reviewer` |
|---|:---:|:---:|:---:|:---:|
| Create case | ✓ | ✓ | — | — |
| Archive case | ✓ | ✓ | — | — |
| Manage case members | ✓ | ✓ | — | — |
| Upload evidence | ✓ | ✓ | ✓ | — |
| View evidence | ✓ | ✓ | ✓ | ✓ |
| Download evidence | ✓ | ✓ | ✓ | ✓ |
| Delete evidence (Phase 2+) | ✓ | ✓ | — | — |
| View audit log | ✓ | ✓ | ✓ | ✓ |
| Verify audit chain | ✓ | ✓ | ✓ | — |
| Manage platform users | ✓ | — | — | — |

---

## 5. Evidence Status Lifecycle

```
UPLOAD REQUEST
      │
      ▼
  [PENDING] ──► worker picks up job ──► [PARSING]
                                            │
                              ┌─────────────┤
                              │             │
                        [PARSED]     [PARSE_FAILED]
                              
  (unsupported MIME → set directly to [UNSUPPORTED])
```

---

## 6. Key Invariants

1. `evidence.sha256_hash` is immutable after insert.
2. `evidence.cas_path` is immutable after insert.
3. `audit_log` rows are never updated or deleted via application paths.
4. `audit_log.entry_hash` is verified on every read in the chain-verification path.
5. `case_memberships` uses soft delete (`removed_at`) to preserve history.
6. `users` uses soft deactivation (`is_active = false`) — rows are never deleted.
7. A `(case_id, sha256_hash)` unique constraint on `evidence` prevents duplicate uploads of the same file to the same case.
