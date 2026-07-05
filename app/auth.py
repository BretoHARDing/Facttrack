import bcrypt, jwt, uuid
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.models import User
security = HTTPBearer()
def hash_pw(pw: str) -> str: return bcrypt.hashpw(pw.encode(), bcrypt.gensalt(12)).decode()
def verify_pw(pw: str, h: str) -> bool: return bcrypt.checkpw(pw.encode(), h.encode())
def create_token(uid: str, role: str) -> str:
    return jwt.encode({"sub": uid, "role": role, "exp": datetime.now(timezone.utc)+timedelta(minutes=30)},
                      settings.JWT_SECRET, algorithm="HS256")
async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security),
                           db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(creds.credentials, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = uuid.UUID(payload["sub"])
    except Exception: raise HTTPException(401, "Invalid token")
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active: raise HTTPException(401, "User not found")
    await db.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": str(user.id)})
    return user
