# FACTTRACK — Phase 1 API Surface

All endpoints are prefixed with `/api/v1`. Authentication uses a JWT Bearer token in the `Authorization` header unless noted. Responses follow standard HTTP semantics. All timestamps are ISO 8601 UTC.

---

## Auth — `/api/v1/auth`

### POST /register

Register a new user account.

**Request**
```json
{
  "email": "analyst@example.com",
  "password": "minimum12chars!"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "email": "analyst@example.com",
  "platform_role": "case_investigator"
}
```

**Errors**: `400` email already registered, `422` validation failure.

---

### POST /login

Authenticate and obtain tokens. If MFA is enabled, returns `mfa_required: true` and no tokens.

**Request**
```json
{
  "email": "analyst@example.com",
  "password": "minimum12chars!",
  "totp_code": "123456"
}
```

**Response `200` (MFA not enabled or code provided)**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "mfa_required": false
}
```

**Response `200` (MFA enabled, no code supplied)**
```json
{
  "access_token": null,
  "token_type": "bearer",
  "mfa_required": true
}
```

Refresh token is returned as an `HttpOnly` cookie (`refresh_token`).

**Errors**: `401` invalid credentials, `403` account inactive.

---

### POST /mfa/setup *(requires auth)*

Generate a TOTP secret and provisioning URI for the authenticated user. Does not enable MFA until verified.

**Response `200`**
```json
{
  "totp_uri": "otpauth://totp/FACTTRACK:analyst@example.com?secret=BASE32&issuer=FACTTRACK",
  "qr_code_base64": "iVBORw0KGgo..."
}
```

---

### POST /mfa/verify *(requires auth)*

Verify a TOTP code and activate MFA for the account.

**Request**
```json
{ "totp_code": "123456" }
```

**Response `200`**
```json
{ "mfa_enabled": true }
```

**Errors**: `400` invalid code.

---

### POST /refresh

Exchange a valid refresh token for a new access token. Refresh token is rotated.

**Request** (cookie `refresh_token` or body)
```json
{ "refresh_token": "opaque-token" }
```

**Response `200`**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Errors**: `401` token expired or revoked.

---

### POST /logout *(requires auth)*

Revoke the current refresh token.

**Response `200`**
```json
{ "message": "logged out" }
```

---

## Cases — `/api/v1/cases`

### POST / *(requires auth)*

Create a new case workspace. Creator is automatically added as `case_owner`.

**Request**
```json
{
  "name": "Operation Example",
  "description": "Optional description"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "name": "Operation Example",
  "description": "Optional description",
  "status": "active",
  "created_by": "uuid",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

---

### GET / *(requires auth)*

List cases the authenticated user is a member of.

**Response `200`**
```json
[{ ...CaseResponse }, ...]
```

---

### GET /{case_id} *(requires case membership)*

Get a single case.

**Response `200`**: `CaseResponse`

**Errors**: `403` not a member, `404` not found.

---

### PATCH /{case_id} *(requires case_owner)*

Update case name or description.

**Request**
```json
{ "name": "New Name", "description": "Updated" }
```

**Response `200`**: `CaseResponse`

---

### POST /{case_id}/archive *(requires case_owner)*

Archive a case.

**Response `200`**: `CaseResponse` with `status: "archived"`

---

### GET /{case_id}/members *(requires case membership)*

List active members of a case.

**Response `200`**
```json
[{
  "id": "uuid",
  "case_id": "uuid",
  "user_id": "uuid",
  "case_role": "case_investigator",
  "added_at": "2024-01-01T00:00:00Z"
}]
```

---

### POST /{case_id}/members *(requires case_owner)*

Add a member to the case.

**Request**
```json
{
  "user_id": "uuid",
  "case_role": "case_investigator"
}
```

**Response `201`**: `MemberResponse`

**Errors**: `409` already a member.

---

### DELETE /{case_id}/members/{user_id} *(requires case_owner)*

Remove a member from the case (soft delete — sets `removed_at`).

**Response `204`**

---

## Evidence — `/api/v1/cases/{case_id}/evidence`

### POST / *(requires case membership, investigator or above)*

Upload an evidence file. Accepts `multipart/form-data`.

**Form fields**
- `file`: binary file upload (required)
- `description`: string (optional)
- `tags`: comma-separated string (optional)

**Response `202`**
```json
{
  "id": "uuid",
  "case_id": "uuid",
  "original_filename": "document.pdf",
  "mime_type": "application/pdf",
  "file_size": 204800,
  "sha256_hash": "abcdef1234...",
  "status": "PENDING",
  "description": null,
  "tags": [],
  "uploaded_at": "2024-01-01T00:00:00Z",
  "parsed_at": null
}
```

**Errors**: `409` duplicate file already in this case (same SHA-256), `413` file too large.

---

### GET / *(requires case membership)*

List evidence in a case.

**Query params**: `page` (default 1), `page_size` (default 50), `status`, `mime_type`

**Response `200`**
```json
{
  "items": [{ ...EvidenceResponse }],
  "total": 42,
  "page": 1,
  "page_size": 50
}
```

---

### GET /{evidence_id} *(requires case membership)*

Get a single evidence record. Emits `EVIDENCE_VIEWED` audit event.

**Response `200`**: `EvidenceResponse`

---

### GET /{evidence_id}/download *(requires case membership)*

Download the original file from CAS. Verifies SHA-256 before streaming. Emits `EVIDENCE_DOWNLOADED` audit event.

**Response `200`**: binary file stream with `Content-Type`, `Content-Disposition: attachment`

**Errors**: `409` hash mismatch (CAS integrity failure), `404` file not found.

---

### GET /{evidence_id}/artifacts *(requires case membership)*

Get parsed artifacts for an evidence item.

**Response `200`**
```json
[{
  "id": "uuid",
  "evidence_id": "uuid",
  "artifact_type": "EXTRACTED_TEXT",
  "content": "Full extracted text...",
  "metadata_": { "page_count": 12, "ocr_used": false },
  "created_at": "2024-01-01T00:00:00Z"
}]
```

---

## Audit — `/api/v1/audit`

### GET /cases/{case_id} *(requires case membership)*

Retrieve audit log entries for a case, newest first.

**Query params**: `page`, `page_size`, `event_type`

**Response `200`**
```json
[{
  "id": "uuid",
  "prev_hash": "abcdef...",
  "event_type": "EVIDENCE_UPLOADED",
  "actor_id": "uuid",
  "case_id": "uuid",
  "subject_id": "uuid",
  "payload": { "filename": "doc.pdf", "sha256": "abc..." },
  "created_at": "2024-01-01T00:00:00Z",
  "entry_hash": "fedcba..."
}]
```

---

### GET /verify *(requires auth)*

Verify the integrity of the full audit chain.

**Response `200`**
```json
{
  "valid": true,
  "total_entries": 1042,
  "first_entry_id": "uuid",
  "last_entry_id": "uuid",
  "error": null
}
```

---

### GET /verify/cases/{case_id} *(requires case membership)*

Verify the audit chain scoped to a case. Emits `AUDIT_VERIFIED` event.

**Response `200`**: `AuditVerifyResponse`

---

## Health — `/api/v1`

### GET /health

Liveness probe. No auth required.

**Response `200`**
```json
{ "status": "ok", "environment": "development" }
```

---

### GET /health/db

Check database connectivity. No auth required.

**Response `200`**
```json
{ "status": "ok", "latency_ms": 2 }
```

**Response `503`** if database is unreachable.

---

### GET /health/redis

Check Redis connectivity. No auth required.

**Response `200`**
```json
{ "status": "ok", "latency_ms": 1 }
```

**Response `503`** if Redis is unreachable.

---

## Common Error Format

All error responses use:
```json
{
  "detail": "Human-readable error message"
}
```

For validation errors (`422`):
```json
{
  "detail": [
    { "loc": ["body", "email"], "msg": "value is not a valid email address", "type": "value_error" }
  ]
}
```

---

## Pagination

List endpoints that support pagination return:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 50
}
```

---

## Authentication Flow Summary

```
Register → Login (get access_token + refresh_token cookie)
         → [if MFA required] POST /mfa/verify with totp_code
         → Use access_token in Authorization: Bearer <token>
         → When expired: POST /refresh → new access_token
         → POST /logout to revoke refresh_token
```
