import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEventType, Evidence, EvidenceStatus
from app.services.audit_service import audit_service
from app.services.cas_service import CASService
from app.utils.hashing import sha256_hex


async def ingest_evidence(
    db: AsyncSession,
    cas_service: CASService,
    file_data: bytes,
    filename: str,
    mime_type: str,
    case_id: str,
    user_id: str,
    description: Optional[str] = None,
    tags: Optional[list[str]] = None,
) -> Evidence:
    """
    1. Compute SHA-256 of file_data
    2. Write to CAS (idempotent)
    3. Check for duplicate in same case (case_id + sha256_hash unique)
    4. Create Evidence record with status=PENDING
    5. Emit audit event EVIDENCE_UPLOADED
    6. Enqueue arq parse job
    7. Return Evidence record
    """
    file_hash = sha256_hex(file_data)
    cas_path = await cas_service.write(file_data, file_hash)

    case_uuid = uuid.UUID(case_id)
    result = await db.execute(
        select(Evidence).where(
            Evidence.case_id == case_uuid,
            Evidence.sha256_hash == file_hash,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError(f"Duplicate evidence: file with hash {file_hash} already exists in this case")

    evidence = Evidence(
        case_id=case_uuid,
        uploaded_by=uuid.UUID(user_id),
        original_filename=filename,
        mime_type=mime_type,
        file_size=len(file_data),
        sha256_hash=file_hash,
        cas_path=cas_path,
        status=EvidenceStatus.PENDING.value,
        description=description,
        tags=tags or [],
    )
    db.add(evidence)
    await db.flush()

    await audit_service.record(
        db=db,
        event_type=AuditEventType.EVIDENCE_UPLOADED,
        actor_id=uuid.UUID(user_id),
        case_id=case_uuid,
        subject_id=evidence.id,
        payload={
            "filename": filename,
            "mime_type": mime_type,
            "sha256_hash": file_hash,
            "file_size": len(file_data),
        },
    )

    return evidence
