from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import async_session
from app.api import auth_routes, cases_routes, evidence_routes, ai_routes
app = FastAPI(title="FACTTRACK", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_routes.router)
app.include_router(cases_routes.router)
app.include_router(evidence_routes.router)
app.include_router(ai_routes.router)
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str

@app.get("/health", response_model=HealthResponse, tags=["default"])
async def health():
    db_status = "ok"
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "unavailable"
    return {"status": "healthy" if db_status == "ok" else "degraded",
            "version": app.version, "database": db_status}
