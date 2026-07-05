import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Evidence, EvidenceType, CaseWorkspace
from app.cas import cas_store
from app.audit import audit_logger
from app.auth import get_current_user
from ingestion.parsers import PDFParser, EmailParser, SpreadsheetParser, ParseResult
router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])
MIME_MAP = {"application/pdf": EvidenceType.PDF, "message/rfc822": EvidenceType.EMAIL,
            "text/csv": EvidenceType.SPREADSHEET, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": EvidenceType.SPREADSHEET}
MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB

def _parse_uuid(value: str, label: str) -> uuid.UUID:
    try: return uuid.UUID(value)
    except ValueError: raise HTTPException(422, f"Invalid {label}")

@router.post("/upload")
async def upload(file: UploadFile = File(...), case_id: str = Form(...), title: str = Form(...),
                 description: str | None = Form(None), db: AsyncSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    case_uuid = _parse_uuid(case_id, "case_id")
    case = (await db.execute(select(CaseWorkspace).where(CaseWorkspace.id == case_uuid))).scalar_one_or_none()
    if not case: raise HTTPException(404, "Case not found")
    data = await file.read()
    if not data: raise HTTPException(422, "Empty file")
    if len(data) > MAX_UPLOAD_BYTES: raise HTTPException(413, f"File exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit")
    cas_hash = await cas_store.store(data)
    mime = file.content_type or "application/octet-stream"
    etype = MIME_MAP.get(mime, EvidenceType.OTHER)
    if etype == EvidenceType.PDF: parsed = PDFParser().parse(data)
    elif etype == EvidenceType.EMAIL: parsed = EmailParser().parse(data)
    elif etype == EvidenceType.SPREADSHEET: parsed = SpreadsheetParser().parse(data, mime)
    else: parsed = ParseResult(text=data.decode("utf-8", errors="replace")[:10000])
    ev = Evidence(case_id=case_uuid, title=title, evidence_type=etype, original_filename=file.filename or "unnamed",
                  mime_type=mime, file_size_bytes=len(data), cas_hash=cas_hash,
                  metadata_json=parsed.metadata, extracted_text=parsed.text or None, uploaded_by=user.id)
    db.add(ev); await db.flush()
    await audit_logger.log(db, user.id, "evidence_uploaded", case_id=ev.case_id, evidence_id=ev.id,
                           details={"filename": file.filename, "size": len(data), "hash": cas_hash[:16]})
    await db.commit()
    return {"evidence_id": str(ev.id), "cas_hash": cas_hash,
            "status": "indexed" if parsed.text else "failed", "parse_errors": parsed.errors}

@router.get("/case/{case_id}")
async def list_evidence(case_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    res = await db.execute(select(Evidence).where(Evidence.case_id == case_id).order_by(Evidence.created_at.desc()))
    return [{"evidence_id": str(e.id), "title": e.title, "type": e.evidence_type.value,
             "filename": e.original_filename, "size_bytes": e.file_size_bytes,
             "cas_hash": e.cas_hash, "indexed": e.extracted_text is not None,
             "created_at": e.created_at.isoformat()} for e in res.scalars().all()]

@router.get("/{evidence_id}/download")
async def download_evidence(evidence_id: uuid.UUID, db: AsyncSession = Depends(get_db),
                            user: User = Depends(get_current_user)):
    ev = (await db.execute(select(Evidence).where(Evidence.id == evidence_id))).scalar_one_or_none()
    if not ev: raise HTTPException(404, "Evidence not found")
    try: data = await cas_store.read(ev.cas_hash)
    except FileNotFoundError: raise HTTPException(410, "Stored file missing from CAS")
    except ValueError: raise HTTPException(500, "CAS integrity check failed")
    await audit_logger.log(db, user.id, "evidence_downloaded", case_id=ev.case_id, evidence_id=ev.id,
                           details={"filename": ev.original_filename})
    await db.commit()
    return Response(content=data, media_type=ev.mime_type,
                    headers={"Content-Disposition": f'attachment; filename="{ev.original_filename}"'})
