from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as exc:
        return {"status": "error", "db": str(exc)}


@router.get("/health/redis")
async def health_redis():
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await client.ping()
        await client.aclose()
        return {"status": "ok", "redis": "connected"}
    except Exception as exc:
        return {"status": "error", "redis": str(exc)}
