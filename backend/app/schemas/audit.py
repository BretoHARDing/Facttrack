import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models import AuditEventType


class AuditLogEntry(BaseModel):
    id: uuid.UUID
    prev_hash: str
    event_type: AuditEventType
    actor_id: Optional[uuid.UUID]
    case_id: Optional[uuid.UUID]
    subject_id: Optional[uuid.UUID]
    payload: dict[str, Any]
    created_at: datetime
    entry_hash: str

    model_config = {"from_attributes": True}


class AuditVerifyResponse(BaseModel):
    valid: bool
    total_entries: int
    first_entry_id: Optional[uuid.UUID]
    last_entry_id: Optional[uuid.UUID]
    error: Optional[str] = None
