import hashlib


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_stream(file_path: str) -> str:
    """Compute SHA-256 of a file by streaming it."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_audit_entry_hash(
    entry_id: str,
    prev_hash: str,
    event_type: str,
    actor_id: str | None,
    payload: dict,
    created_at: str,
) -> str:
    canonical = f"{entry_id}|{prev_hash}|{event_type}|{actor_id or ''}|{payload}|{created_at}"
    return sha256_hex(canonical.encode())
