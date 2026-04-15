import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEventType, AuditLog
from app.utils.hashing import compute_audit_entry_hash

SENTINEL_HASH = "0" * 64


class AuditService:
    async def record(
        self,
        db: AsyncSession,
        event_type: AuditEventType,
        actor_id: Optional[uuid.UUID] = None,
        case_id: Optional[uuid.UUID] = None,
        subject_id: Optional[uuid.UUID] = None,
        payload: Optional[dict] = None,
    ) -> AuditLog:
        """Append an entry to the audit chain."""
        if payload is None:
            payload = {}

        # Fetch the last entry_hash for chain linkage
        result = await db.execute(
            select(AuditLog.entry_hash)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .limit(1)
        )
        last_row = result.first()
        prev_hash = last_row[0] if last_row else SENTINEL_HASH

        entry_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        created_at_str = created_at.isoformat()

        entry_hash = compute_audit_entry_hash(
            entry_id=entry_id,
            prev_hash=prev_hash,
            event_type=event_type.value if isinstance(event_type, AuditEventType) else event_type,
            actor_id=str(actor_id) if actor_id else None,
            payload=payload,
            created_at=created_at_str,
        )

        log_entry = AuditLog(
            id=uuid.UUID(entry_id),
            prev_hash=prev_hash,
            event_type=event_type.value if isinstance(event_type, AuditEventType) else event_type,
            actor_id=actor_id,
            case_id=case_id,
            subject_id=subject_id,
            payload=payload,
            created_at=created_at,
            entry_hash=entry_hash,
        )
        db.add(log_entry)
        await db.flush()
        return log_entry

    async def verify_chain(
        self,
        db: AsyncSession,
        case_id: Optional[uuid.UUID] = None,
    ) -> dict:
        """Traverse audit_logs in created_at order, recompute entry_hash, check linkage."""
        query = select(AuditLog).order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        if case_id is not None:
            query = query.where(AuditLog.case_id == case_id)

        result = await db.execute(query)
        entries = result.scalars().all()

        if not entries:
            return {
                "valid": True,
                "total": 0,
                "first_id": None,
                "last_id": None,
                "error": None,
            }

        expected_prev = SENTINEL_HASH
        for entry in entries:
            if entry.prev_hash != expected_prev:
                return {
                    "valid": False,
                    "total": len(entries),
                    "first_id": entries[0].id,
                    "last_id": entries[-1].id,
                    "error": f"Chain broken at entry {entry.id}: prev_hash mismatch",
                }

            recomputed = compute_audit_entry_hash(
                entry_id=str(entry.id),
                prev_hash=entry.prev_hash,
                event_type=entry.event_type,
                actor_id=str(entry.actor_id) if entry.actor_id else None,
                payload=entry.payload,
                created_at=entry.created_at.isoformat(),
            )
            if recomputed != entry.entry_hash:
                return {
                    "valid": False,
                    "total": len(entries),
                    "first_id": entries[0].id,
                    "last_id": entries[-1].id,
                    "error": f"Hash mismatch at entry {entry.id}",
                }

            expected_prev = entry.entry_hash

        return {
            "valid": True,
            "total": len(entries),
            "first_id": entries[0].id,
            "last_id": entries[-1].id,
            "error": None,
        }


audit_service = AuditService()
