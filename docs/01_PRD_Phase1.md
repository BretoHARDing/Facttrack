# FACTTRACK — Phase 1 Product Requirements Document

## 1. Purpose

FACTTRACK is a secure forensic evidence platform for legal and investigative work. Its purpose is to provide investigators and legal teams with a trustworthy, auditable system for ingesting, storing, searching, and reviewing evidence — with a verifiable chain of custody from first upload through every subsequent access or transformation.

Phase 1 delivers the operational trust foundation. Every capability built in later phases (AI-assisted analysis, timeline intelligence, contradiction detection, RAG-based Q&A) depends on the integrity guarantees established here.

---

## 2. Phase 1 Scope

### In scope

| Area | Deliverables |
|---|---|
| Authentication | Secure registration, login, JWT access + refresh tokens, TOTP MFA |
| Case workspaces | Create, list, update, archive cases; strict member-scoped access |
| Case membership | Assign/remove members; role-based permissions within a case |
| Evidence ingestion | Upload API, hash-first processing, content-addressed storage |
| Evidence parsing | MIME-routed parsers: PDF (+ OCR fallback), email, spreadsheet, plain text |
| Evidence retrieval | Download original and derived artifacts with integrity verification |
| Audit logging | Append-only tamper-evident log for all significant system events |
| Audit verification | API and CLI tool to verify the integrity of the audit chain |
| Search baseline | Full-text search over extracted evidence content within a case |
| Developer environment | Docker Compose stack; repeatable local setup |
| Tests | Access control, ingestion, CAS integrity, audit chain validity |

### Out of scope for Phase 1

- Contradiction detection engine
- Timeline intelligence
- Multimodal/RAG search
- Knowledge graph
- C2PA provenance integration
- Attribute-based access control beyond RBAC + case membership
- Offline-first sync
- WebAuthn / FIDO2 (deferred to Phase 1.5)
- Merkle batch sealing (architecture is designed to accommodate it; implementation is deferred)

---

## 3. User Roles

| Role | Description |
|---|---|
| `platform_admin` | Full system access; manages users and global settings; cannot view case evidence unless also a case member |
| `case_owner` | Creates and owns a case workspace; can manage membership and all evidence within the case |
| `case_investigator` | Full read/write access to case evidence; cannot manage membership |
| `case_reviewer` | Read-only access to case evidence and audit logs; cannot upload or annotate |

Role assignments are case-scoped. A user may hold different roles in different cases.

---

## 4. Supported Evidence Types (Phase 1)

| MIME Type / Format | Parser | Extracted Artifacts |
|---|---|---|
| `application/pdf` | PDF text extractor + Tesseract OCR fallback | Extracted text, page count, OCR confidence flag |
| `message/rfc822` (`.eml`) | Email parser | Headers, sender, recipients, body text, attachment list |
| `application/vnd.ms-excel`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Spreadsheet parser | Normalized text representation, sheet/row/column structure |
| `text/plain`, `text/csv` | Plain text / CSV parser | Raw text content |
| All other types | Raw store only | No text extraction; original preserved |

---

## 5. Trust and Integrity Guarantees

1. **Immutability**: Once ingested, the original file bytes are never modified. The content-addressed store (CAS) uses SHA-256 to address files; writing to an existing hash is rejected.
2. **Hash-first ingestion**: SHA-256 is computed over raw bytes before any parsing or storage operation begins. The hash is stored with the evidence record.
3. **Audit chain integrity**: Each audit log entry records the SHA-256 of the previous entry, creating a forward-only hash chain. Gaps or modifications are detectable.
4. **Case isolation**: Row-level security (RLS) in PostgreSQL ensures that queries cannot return evidence outside the authenticated user's case memberships, regardless of application-layer logic.
5. **Download integrity**: Evidence downloads are verified against the stored hash before being served.
6. **Non-repudiation**: All audit entries include the acting user's ID, the timestamp, and the event type. They cannot be deleted through normal application paths.

---

## 6. Security Requirements

| Requirement | Detail |
|---|---|
| Passwords | Bcrypt with cost ≥ 12; minimum 12 characters |
| JWT access tokens | Short-lived (15 min); signed with RS256 |
| Refresh tokens | Long-lived (7 days); stored hashed; single-use rotation |
| MFA | TOTP (RFC 6238); enforced for all accounts by default |
| Transport | TLS 1.2+ required in production; enforced at reverse proxy |
| RLS | PostgreSQL row-level security on all evidence, audit, and membership tables |
| Session invalidation | Refresh token revocation propagates immediately |
| Rate limiting | Auth endpoints: 10 req/min per IP; upload endpoint: configurable |
| Secret management | All secrets via environment variables or a secrets manager; never in source |
| CAS write protection | CAS directory is append-only; no delete API exposed in Phase 1 |

---

## 7. Operational Constraints

- The system must run locally using Docker Compose with a single `docker compose up` command.
- Database migrations must be versioned and run automatically on startup in development.
- The application must be stateless at the API layer (all state in PostgreSQL and Redis).
- File storage in Phase 1 uses local filesystem CAS; the interface must support future swap to S3-compatible object storage.
- Parsing is asynchronous; evidence records transition through defined status states.
- All configuration is via environment variables with documented defaults.

---

## 8. Acceptance Criteria

Phase 1 is complete when the following are all true:

- [ ] A new user can register, log in, and enable MFA.
- [ ] An authenticated user can create a case workspace.
- [ ] A case owner can invite members and assign roles.
- [ ] An authenticated case member can upload a supported evidence file.
- [ ] The upload endpoint returns the SHA-256 hash of the stored file.
- [ ] The same file uploaded twice yields the same hash and is not stored twice (deduplication).
- [ ] Parsed text and metadata are accessible via the evidence API.
- [ ] A user who is not a case member cannot access any evidence in that case (RLS-verified test).
- [ ] An evidence file can be downloaded and its hash matches the stored value.
- [ ] Every upload, download, view, login, and role change produces an audit log entry.
- [ ] The audit chain can be verified end-to-end by the verification endpoint.
- [ ] A tampered audit entry causes verification to fail.
- [ ] The full stack starts from cold with `docker compose up`.
- [ ] All acceptance-critical tests pass in CI.
