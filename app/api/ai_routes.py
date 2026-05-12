from fastapi import APIRouter, Depends
from pydantic import BaseModel
import uuid
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user
from app.models import User, Evidence
from app.ai_pipeline import ContradictionEngine
from app.llm_client import extract_nsw_matrix
from fastapi import HTTPException
from app.ai_pipeline import ContradictionEngine

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])

class ContradictionReq(BaseModel):
    claim1: str
    claim2: str

class ContradictionRes(BaseModel):
    contradiction_probability: float
    overlap_score: float
    conclusion: str

engine = ContradictionEngine()

@router.post("/contradiction", response_model=ContradictionRes)
async def detect_contradiction(req: ContradictionReq, user: User = Depends(get_current_user)):
    return engine.analyze(req.claim1, req.claim2)

class CaseCheckReq(BaseModel):
    case_id: uuid.UUID
    claim: str

class EvidenceContradiction(BaseModel):
    evidence_id: uuid.UUID
    filename: str
    contradicting_sentence: str
    contradiction_probability: float

class CaseCheckRes(BaseModel):
    claim: str
    contradictions_found: List[EvidenceContradiction]

@router.post("/evidence-check", response_model=CaseCheckRes)
async def check_evidence(req: CaseCheckReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Evidence).where(Evidence.case_id == req.case_id))
    evidence_list = res.scalars().all()
    
    contradictions = []
    for ev in evidence_list:
        if not ev.extracted_text: continue
        sentences = ev.extracted_text.replace('\n', '.').split('.')
        for sentence in sentences:
            if len(sentence.strip()) < 10: continue
            analysis = engine.analyze(req.claim, sentence)
            if analysis["contradiction_probability"] > 0.5:
                contradictions.append(EvidenceContradiction(
                    evidence_id=ev.id,
                    filename=ev.original_filename,
                    contradicting_sentence=sentence.strip(),
                    contradiction_probability=analysis["contradiction_probability"]
                ))
                
    contradictions.sort(key=lambda x: x.contradiction_probability, reverse=True)
    return CaseCheckRes(claim=req.claim, contradictions_found=contradictions[:10])

class MatrixExtractReq(BaseModel):
    evidence_id: uuid.UUID

class MatrixExtractRes(BaseModel):
    evidence_id: uuid.UUID
    matrix_output: str

@router.post("/extract-matrix", response_model=MatrixExtractRes)
async def run_matrix_extraction(req: MatrixExtractReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ev = await db.execute(select(Evidence).where(Evidence.id == req.evidence_id))
    evidence = ev.scalar_one_or_none()
    if not evidence or not evidence.extracted_text:
        raise HTTPException(404, "Evidence not found or has no extracted text")
        
    output = await extract_nsw_matrix(evidence.extracted_text)
    return MatrixExtractRes(evidence_id=req.evidence_id, matrix_output=output)
