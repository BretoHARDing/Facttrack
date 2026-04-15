import base64
import io
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import pyotp
import qrcode
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AuditEventType, PlatformRole, RefreshToken, User
from app.utils.hashing import sha256_hex

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, email: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])


def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, token_hash)."""
    raw = secrets.token_urlsafe(64)
    hashed = sha256_hex(raw.encode())
    return raw, hashed


async def register_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=email,
        password_hash=hash_password(password),
        platform_role=PlatformRole.case_investigator.value,
    )
    db.add(user)
    await db.flush()
    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    totp_code: Optional[str] = None,
) -> dict:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    if not user.is_active:
        raise ValueError("Account is inactive")

    if user.totp_enabled:
        if not totp_code:
            return {"mfa_required": True, "user": user}
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(totp_code):
            raise ValueError("Invalid TOTP code")

    access_token = create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.platform_role,
    )
    raw_refresh, refresh_hash = create_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    token_record = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=expires_at,
    )
    db.add(token_record)
    await db.flush()

    return {
        "mfa_required": False,
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "user": user,
    }


async def refresh_access_token(db: AsyncSession, raw_refresh_token: str) -> str:
    token_hash = sha256_hex(raw_refresh_token.encode())
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token_record = result.scalar_one_or_none()

    if not token_record:
        raise ValueError("Refresh token not found")
    if token_record.revoked_at is not None:
        raise ValueError("Refresh token has been revoked")
    if token_record.expires_at < datetime.now(timezone.utc):
        raise ValueError("Refresh token has expired")

    user_result = await db.execute(
        select(User).where(User.id == token_record.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")

    return create_access_token(
        user_id=str(user.id),
        email=user.email,
        role=user.platform_role,
    )


async def setup_mfa(db: AsyncSession, user: User) -> dict:
    secret = pyotp.random_base32()
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        user.email, issuer_name="FACTTRACK"
    )

    qr = qrcode.make(totp_uri)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    user.totp_secret = secret
    db.add(user)
    await db.flush()

    return {"totp_uri": totp_uri, "qr_code_base64": qr_base64}


async def verify_mfa(db: AsyncSession, user: User, totp_code: str) -> bool:
    if not user.totp_secret:
        return False
    totp = pyotp.TOTP(user.totp_secret)
    if totp.verify(totp_code):
        user.totp_enabled = True
        db.add(user)
        await db.flush()
        return True
    return False


async def revoke_refresh_tokens(db: AsyncSession, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
    )
    tokens = result.scalars().all()
    now = datetime.now(timezone.utc)
    for token in tokens:
        token.revoked_at = now
    await db.flush()
