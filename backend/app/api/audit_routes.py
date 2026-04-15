import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, set_rls_user
from app.dependencies.auth import get_current_user, require_case_access
from app.models import AuditEventType, AuditLog, CaseMembership
from app.schemas.audit import AuditLogEntry, AuditVerifyResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/cases/{case_id}", response_model=list[AuditLogEntry])
async def list_case_audit_logs(
    case_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
):
    await set_rls_user(db, str(current_user.id))
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.case_id == case_id)
        .order_by(AuditLog.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/verify", response_model=AuditVerifyResponse)
async def verify_full_chain(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))
    result = await audit_service.verify_chain(db)
    await audit_service.record(
        db=db,
        event_type=AuditEventType.AUDIT_VERIFIED,
        actor_id=current_user.id,
        payload={"valid": result["valid"], "total": result["total"]},
    )
    await db.commit()
    return AuditVerifyResponse(
        valid=result["valid"],
        total_entries=result["total"],
        first_entry_id=result["first_id"],
        last_entry_id=result["last_id"],
        error=result["error"],
    )


@router.get("/verify/cases/{case_id}", response_model=AuditVerifyResponse)
async def verify_case_chain(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
):
    await set_rls_user(db, str(current_user.id))
    result = await audit_service.verify_chain(db, case_id=case_id)
    await audit_service.record(
        db=db,
        event_type=AuditEventType.AUDIT_VERIFIED,
        actor_id=current_user.id,
        case_id=case_id,
        payload={"valid": result["valid"], "total": result["total"]},
    )
    await db.commit()
    return AuditVerifyResponse(
        valid=result["valid"],
        total_entries=result["total"],
        first_entry_id=result["first_id"],
        last_entry_id=result["last_id"],
        error=result["error"],
    )
