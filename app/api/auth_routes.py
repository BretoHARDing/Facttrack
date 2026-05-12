from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, UserRole
from app.auth import hash_pw, verify_pw, create_token, get_current_user
router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
class RegisterReq(BaseModel): email: EmailStr; password: str = Field(..., min_length=8); display_name: str
class LoginReq(BaseModel): email: EmailStr; password: str
class RegisterRes(BaseModel): user_id: str; access_token: str
class LoginRes(BaseModel): access_token: str; token_type: str
@router.post("/register", response_model=RegisterRes)
async def register(req: RegisterReq, db: AsyncSession = Depends(get_db)):
    if (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none():
        raise HTTPException(409, "Email exists")
    user = User(email=req.email, display_name=req.display_name, password_hash=hash_pw(req.password), role=UserRole.INVESTIGATOR)
    db.add(user); await db.commit(); await db.refresh(user)
    return {"user_id": str(user.id), "access_token": create_token(str(user.id), user.role.value)}
@router.post("/login", response_model=LoginRes)
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    user = (await db.execute(select(User).where(User.email == req.email))).scalar_one_or_none()
    if not user or not verify_pw(req.password, user.password_hash): raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(str(user.id), user.role.value), "token_type": "bearer"}
