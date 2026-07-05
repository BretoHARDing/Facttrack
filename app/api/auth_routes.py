from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, UserRole
from app.audit import audit_logger
from app.auth import hash_pw, verify_pw, create_token, get_current_user
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
# Dummy hash keeps login timing constant whether or not the email exists
_DUMMY_HASH = hash_pw("timing-equalizer-placeholder")
class RegisterReq(BaseModel): email: EmailStr; password: str = Field(..., min_length=8); display_name: str = Field(..., min_length=1, max_length=255)
class LoginReq(BaseModel): email: EmailStr; password: str
class RegisterRes(BaseModel): user_id: str; access_token: str; token_type: str = "bearer"
class LoginRes(BaseModel): access_token: str; token_type: str
class MeRes(BaseModel): user_id: str; email: str; display_name: str; role: str
@router.post("/register", response_model=RegisterRes)
async def register(req: RegisterReq, db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none():
        raise HTTPException(409, "Email exists")
    user = User(email=req.email, display_name=req.display_name, password_hash=hash_pw(req.password), role=UserRole.INVESTIGATOR)
    db.add(user); await db.flush()
    await audit_logger.log(db, user.id, "user_registered", details={"email": req.email})
    await db.commit(); await db.refresh(user)
    return {"user_id": str(user.id), "access_token": create_token(str(user.id), user.role.value), "token_type": "bearer"}
@router.post("/login", response_model=LoginRes)
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if not verify_pw(req.password, user.password_hash if user else _DUMMY_HASH) or not user:
        raise HTTPException(401, "Invalid credentials")
    if not user.is_active: raise HTTPException(403, "Account disabled")
    await audit_logger.log(db, user.id, "user_login")
    await db.commit()
    return {"access_token": create_token(str(user.id), user.role.value), "token_type": "bearer"}
@router.get("/me", response_model=MeRes)
async def me(user: User = Depends(get_current_user)):
    return {"user_id": str(user.id), "email": user.email, "display_name": user.display_name, "role": user.role.value}
