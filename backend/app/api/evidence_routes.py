import uuid
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, set_rls_user
from app.dependencies.auth import get_current_user, require_case_access
from app.models import AuditEventType, CaseMembership, DerivedArtifact, Evidence
from app.schemas.evidence import ArtifactResponse, EvidenceListResponse, EvidenceResponse
from app.services.audit_service import audit_service
from app.services.cas_service import CASService
from app.services.ingestion_service import ingest_evidence

router = APIRouter(prefix="/api/v1/cases/{case_id}/evidence", tags=["evidence"])


def _get_cas_service() -> CASService:
    return CASService(settings.CAS_ROOT)


@router.post("/", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
    cas_service: CASService = Depends(_get_cas_service),
):
    await set_rls_user(db, str(current_user.id))
    file_data = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    try:
        evidence = await ingest_evidence(
            db=db,
            cas_service=cas_service,
            file_data=file_data,
            filename=file.filename or "unknown",
            mime_type=mime_type,
            case_id=str(case_id),
            user_id=str(current_user.id),
            description=description,
            tags=tag_list,
        )
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    # Enqueue parse job
    try:
        import redis.asyncio as aioredis
        from arq import create_pool
        from arq.connections import RedisSettings

        redis_pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await redis_pool.enqueue_job("parse_evidence_task", str(evidence.id))
        await redis_pool.aclose()
    except Exception:
        pass  # Non-fatal: worker can pick up by polling if needed

    await db.commit()
    await db.refresh(evidence)
    return evidence


@router.get("/", response_model=EvidenceListResponse)
async def list_evidence(
    case_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
):
    await set_rls_user(db, str(current_user.id))

    count_result = await db.execute(
        select(func.count()).select_from(Evidence).where(Evidence.case_id == case_id)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Evidence)
        .where(Evidence.case_id == case_id)
        .order_by(Evidence.uploaded_at.desc())
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return EvidenceListResponse(items=list(items), total=total)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
):
    await set_rls_user(db, str(current_user.id))

    result = await db.execute(
        select(Evidence).where(
            Evidence.id == evidence_id,
            Evidence.case_id == case_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    await audit_service.record(
        db=db,
        event_type=AuditEventType.EVIDENCE_VIEWED,
        actor_id=current_user.id,
        case_id=case_id,
        subject_id=evidence.id,
        payload={"filename": evidence.original_filename},
    )
    await db.commit()
    return evidence


@router.get("/{evidence_id}/download")
async def download_evidence(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
    cas_service: CASService = Depends(_get_cas_service),
):
    await set_rls_user(db, str(current_user.id))

    result = await db.execute(
        select(Evidence).where(
            Evidence.id == evidence_id,
            Evidence.case_id == case_id,
        )
    )
    evidence = result.scalar_one_or_none()
    if not evidence:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")

    file_data = await cas_service.read(evidence.sha256_hash)

    from app.utils.hashing import sha256_hex
    computed = sha256_hex(file_data)
    if computed != evidence.sha256_hash:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File integrity check failed",
        )

    await audit_service.record(
        db=db,
        event_type=AuditEventType.EVIDENCE_DOWNLOADED,
        actor_id=current_user.id,
        case_id=case_id,
        subject_id=evidence.id,
        payload={"filename": evidence.original_filename},
    )
    await db.commit()

    import io
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=evidence.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{evidence.original_filename}"',
            "Content-Length": str(len(file_data)),
        },
    )


@router.get("/{evidence_id}/artifacts", response_model=list[ArtifactResponse])
async def list_artifacts(
    case_id: uuid.UUID,
    evidence_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
):
    await set_rls_user(db, str(current_user.id))

    result = await db.execute(
        select(DerivedArtifact)
        .join(Evidence, DerivedArtifact.evidence_id == Evidence.id)
        .where(
            DerivedArtifact.evidence_id == evidence_id,
            Evidence.case_id == case_id,
        )
    )
    return result.scalars().all()
