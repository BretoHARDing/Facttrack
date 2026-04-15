import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models import ArtifactType, EvidenceStatus


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    sha256_hash: str
    status: EvidenceStatus
    description: Optional[str]
    tags: list[str]
    uploaded_at: datetime
    parsed_at: Optional[datetime]

    model_config = {"from_attributes": True}


class EvidenceListResponse(BaseModel):
    items: list[EvidenceResponse]
    total: int


class ArtifactResponse(BaseModel):
    id: uuid.UUID
    evidence_id: uuid.UUID
    artifact_type: ArtifactType
    content: Optional[str]
    metadata_: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}
