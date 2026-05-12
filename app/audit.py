import hashlib, json, uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog
class AuditLogger:
    async def log(self, db: AsyncSession, user_id: uuid.UUID, action: str,
                  case_id: uuid.UUID | None = None, evidence_id: uuid.UUID | None = None,
                  details: dict | None = None) -> AuditLog:
        res = await db.execute(select(AuditLog.entry_hash).order_by(AuditLog.timestamp.desc()).limit(1))
        prev = res.scalar_one_or_none()
        entry = AuditLog(user_id=user_id, case_id=case_id, evidence_id=evidence_id,
                         action=action, details=details, previous_hash=prev,
                         entry_hash="", timestamp=datetime.now(timezone.utc))
        payload = {"user_id": str(entry.user_id), "action": entry.action,
                   "timestamp": entry.timestamp.isoformat(), "previous_hash": entry.previous_hash, "details": entry.details}
        entry.entry_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        db.add(entry); await db.flush()
        return entry
audit_logger = AuditLogger()
