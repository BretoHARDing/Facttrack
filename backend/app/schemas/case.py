import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models import CaseRole


class CaseCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CaseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CaseResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    status: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemberAdd(BaseModel):
    user_id: uuid.UUID
    case_role: CaseRole = CaseRole.case_investigator


class MemberResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    user_id: uuid.UUID
    case_role: CaseRole
    added_at: datetime

    model_config = {"from_attributes": True}
