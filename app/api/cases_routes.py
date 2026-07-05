import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, CaseWorkspace
from app.audit import audit_logger
from app.auth import get_current_user
router = APIRouter(prefix="/api/v1/cases", tags=["cases"])
class CaseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    jurisdiction: str = Field(..., min_length=1, max_length=10)

def _case_out(case: CaseWorkspace) -> dict:
    return {"case_id": str(case.id), "title": case.title, "jurisdiction": case.jurisdiction,
            "legal_hold": case.legal_hold, "created_by": str(case.created_by),
            "created_at": case.created_at.isoformat()}

@router.post("/")
async def create_case(req: CaseCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    case = CaseWorkspace(title=req.title, jurisdiction=req.jurisdiction, created_by=user.id)
    db.add(case); await db.flush()
    await audit_logger.log(db, user.id, "case_created", case_id=case.id, details={"title": case.title})
    await db.commit(); await db.refresh(case)
    return _case_out(case)

@router.get("/")
async def list_cases(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CaseWorkspace).order_by(CaseWorkspace.created_at.desc()))
    return [_case_out(c) for c in res.scalars().all()]

@router.get("/{case_id}")
async def get_case(case_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    case = (await db.execute(select(CaseWorkspace).where(CaseWorkspace.id == case_id))).scalar_one_or_none()
    if not case: raise HTTPException(404, "Case not found")
    return _case_out(case)
