import logging
import os
import uuid
from datetime import datetime, timezone

import aiofiles
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models import AuditEventType, DerivedArtifact, Evidence, EvidenceStatus
from app.parsers.base import BaseParser
from app.parsers.email_parser import EmailParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.spreadsheet_parser import SpreadsheetParser
from app.parsers.text_parser import TextParser
from app.services.audit_service import audit_service
from app.services.cas_service import CASService

logger = logging.getLogger(__name__)

PARSERS: list[BaseParser] = [
    PDFParser(),
    EmailParser(),
    SpreadsheetParser(),
    TextParser(),
]


def _get_parser(mime_type: str) -> BaseParser | None:
    for parser in PARSERS:
        if parser.can_handle(mime_type):
            return parser
    return None


async def parse_evidence_task(ctx: dict, evidence_id: str) -> None:
    """
    1. Load evidence record
    2. Read file from CAS
    3. Write to temp file
    4. Route to correct parser
    5. Store DerivedArtifact
    6. Update evidence status
    7. Emit audit event
    """
    cas_service: CASService = ctx.get("cas_service") or CASService(settings.CAS_ROOT)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Evidence).where(Evidence.id == uuid.UUID(evidence_id))
        )
        evidence = result.scalar_one_or_none()

        if not evidence:
            logger.error("Evidence %s not found", evidence_id)
            return

        evidence.status = EvidenceStatus.PARSING.value
        await db.commit()

        # Write CAS file to a temporary workspace path within project
        work_dir = os.path.join(settings.CAS_ROOT, "_work")
        os.makedirs(work_dir, exist_ok=True)
        temp_path = os.path.join(work_dir, f"{evidence_id}_{os.path.basename(evidence.original_filename)}")

        try:
            file_data = await cas_service.read(evidence.sha256_hash)
            async with aiofiles.open(temp_path, "wb") as f:
                await f.write(file_data)

            parser = _get_parser(evidence.mime_type)
            if not parser:
                evidence.status = EvidenceStatus.UNSUPPORTED.value
                evidence.parse_error = f"No parser for MIME type: {evidence.mime_type}"
                db.add(evidence)
                await db.commit()
                return

            parse_result = await parser.parse(temp_path, evidence.mime_type)

            artifact = DerivedArtifact(
                evidence_id=evidence.id,
                artifact_type=parse_result.artifact_type,
                content=parse_result.text,
                metadata_=parse_result.metadata,
            )
            db.add(artifact)

            evidence.status = EvidenceStatus.PARSED.value
            evidence.parsed_at = datetime.now(timezone.utc)
            evidence.parse_error = None
            db.add(evidence)

            await audit_service.record(
                db=db,
                event_type=AuditEventType.EVIDENCE_PARSED,
                actor_id=None,
                case_id=evidence.case_id,
                subject_id=evidence.id,
                payload={
                    "artifact_type": parse_result.artifact_type,
                    "warnings": parse_result.warnings,
                },
            )
            await db.commit()

        except Exception as exc:
            logger.exception("Failed to parse evidence %s: %s", evidence_id, exc)
            await db.rollback()
            async with AsyncSessionLocal() as db2:
                result2 = await db2.execute(
                    select(Evidence).where(Evidence.id == uuid.UUID(evidence_id))
                )
                evidence2 = result2.scalar_one_or_none()
                if evidence2:
                    evidence2.status = EvidenceStatus.PARSE_FAILED.value
                    evidence2.parse_error = str(exc)
                    db2.add(evidence2)
                    await audit_service.record(
                        db=db2,
                        event_type=AuditEventType.EVIDENCE_PARSE_FAILED,
                        actor_id=None,
                        case_id=evidence2.case_id,
                        subject_id=evidence2.id,
                        payload={"error": str(exc)},
                    )
                    await db2.commit()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class WorkerSettings:
    functions = [parse_evidence_task]
    redis_settings = settings.REDIS_URL
    job_timeout = 300
    max_jobs = 10
    keep_result = 3600
