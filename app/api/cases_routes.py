from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, CaseWorkspace
from app.auth import get_current_user
router = APIRouter(prefix="/api/v1/cases", tags=["cases"])
class CaseCreate(BaseModel): title: str; jurisdiction: str
@router.post("/")
async def create_case(req: CaseCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    case = CaseWorkspace(title=req.title, jurisdiction=req.jurisdiction, created_by=user.id)
    db.add(case); await db.commit(); await db.refresh(case)
    return {"case_id": str(case.id), "title": case.title}
