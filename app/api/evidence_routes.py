from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
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
@router.post("/upload")
async def upload(file: UploadFile = File(...), case_id: str = Form(...), title: str = Form(...),
                 description: str | None = Form(None), db: AsyncSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    if not await db.execute(select(CaseWorkspace).where(CaseWorkspace.id == case_id)).scalar_one_or_none():
        raise HTTPException(404, "Case not found")
    data = await file.read(); cas_hash = await cas_store.store(data)
    mime = file.content_type or "application/octet-stream"
    etype = MIME_MAP.get(mime, EvidenceType.OTHER)
    if etype == EvidenceType.PDF: parsed = PDFParser().parse(data)
    elif etype == EvidenceType.EMAIL: parsed = EmailParser().parse(data)
    elif etype == EvidenceType.SPREADSHEET: parsed = SpreadsheetParser().parse(data, mime)
    else: parsed = ParseResult(text=data.decode("utf-8", errors="replace")[:10000])
    ev = Evidence(case_id=case_id, title=title, evidence_type=etype, original_filename=file.filename,
                  mime_type=mime, file_size_bytes=len(data), cas_hash=cas_hash,
                  metadata_json=parsed.metadata, extracted_text=parsed.text or None, uploaded_by=user.id)
    db.add(ev); await db.flush()
    await audit_logger.log(db, user.id, "evidence_uploaded", case_id=ev.case_id, evidence_id=ev.id,
                           details={"filename": file.filename, "size": len(data), "hash": cas_hash[:16]})
    await db.commit()
    return {"evidence_id": str(ev.id), "cas_hash": cas_hash, "status": "indexed" if parsed.text else "failed"}
