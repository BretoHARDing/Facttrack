import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, set_rls_user
from app.dependencies.auth import get_current_user, require_case_access
from app.models import AuditEventType, CaseMembership, CaseRole, CaseWorkspace, User
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate, MemberAdd, MemberResponse
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    body: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))
    case = CaseWorkspace(
        name=body.name,
        description=body.description,
        created_by=current_user.id,
    )
    db.add(case)
    await db.flush()

    membership = CaseMembership(
        case_id=case.id,
        user_id=current_user.id,
        case_role=CaseRole.case_owner.value,
        added_by=current_user.id,
    )
    db.add(membership)

    await audit_service.record(
        db=db,
        event_type=AuditEventType.CASE_CREATED,
        actor_id=current_user.id,
        case_id=case.id,
        payload={"name": case.name},
    )
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/", response_model=list[CaseResponse])
async def list_cases(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))
    result = await db.execute(
        select(CaseWorkspace)
        .join(
            CaseMembership,
            CaseMembership.case_id == CaseWorkspace.id,
        )
        .where(
            CaseMembership.user_id == current_user.id,
            CaseMembership.removed_at.is_(None),
        )
        .order_by(CaseWorkspace.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
):
    await set_rls_user(db, str(current_user.id))
    result = await db.execute(
        select(CaseWorkspace).where(CaseWorkspace.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    body: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))

    membership_result = await db.execute(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == current_user.id,
            CaseMembership.removed_at.is_(None),
        )
    )
    membership = membership_result.scalar_one_or_none()
    if not membership or membership.case_role != CaseRole.case_owner.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only case owners can update the case"
        )

    result = await db.execute(
        select(CaseWorkspace).where(CaseWorkspace.id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if body.name is not None:
        case.name = body.name
    if body.description is not None:
        case.description = body.description
    case.updated_at = datetime.now(timezone.utc)
    db.add(case)

    await audit_service.record(
        db=db,
        event_type=AuditEventType.CASE_UPDATED,
        actor_id=current_user.id,
        case_id=case.id,
        payload={"name": body.name, "description": body.description},
    )
    await db.commit()
    await db.refresh(case)
    return case


@router.post("/{case_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def add_member(
    case_id: uuid.UUID,
    body: MemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))

    membership_result = await db.execute(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == current_user.id,
            CaseMembership.removed_at.is_(None),
        )
    )
    caller_membership = membership_result.scalar_one_or_none()
    if not caller_membership or caller_membership.case_role != CaseRole.case_owner.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only case owners can add members"
        )

    existing_result = await db.execute(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == body.user_id,
        )
    )
    existing = existing_result.scalar_one_or_none()
    if existing and existing.removed_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User is already a member"
        )
    if existing:
        existing.removed_at = None
        existing.case_role = body.case_role.value
        membership = existing
    else:
        membership = CaseMembership(
            case_id=case_id,
            user_id=body.user_id,
            case_role=body.case_role.value,
            added_by=current_user.id,
        )
        db.add(membership)

    await db.flush()

    await audit_service.record(
        db=db,
        event_type=AuditEventType.MEMBER_ADDED,
        actor_id=current_user.id,
        case_id=case_id,
        subject_id=body.user_id,
        payload={"case_role": body.case_role.value},
    )
    await db.commit()
    await db.refresh(membership)
    return membership


@router.delete("/{case_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    case_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))

    caller_result = await db.execute(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == current_user.id,
            CaseMembership.removed_at.is_(None),
        )
    )
    caller = caller_result.scalar_one_or_none()
    if not caller or caller.case_role != CaseRole.case_owner.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only case owners can remove members"
        )

    target_result = await db.execute(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == user_id,
            CaseMembership.removed_at.is_(None),
        )
    )
    target = target_result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    target.removed_at = datetime.now(timezone.utc)
    db.add(target)

    await audit_service.record(
        db=db,
        event_type=AuditEventType.MEMBER_REMOVED,
        actor_id=current_user.id,
        case_id=case_id,
        subject_id=user_id,
        payload={},
    )
    await db.commit()


@router.get("/{case_id}/members", response_model=list[MemberResponse])
async def list_members(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _membership: CaseMembership = Depends(require_case_access),
):
    await set_rls_user(db, str(current_user.id))
    result = await db.execute(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.removed_at.is_(None),
        )
    )
    return result.scalars().all()
