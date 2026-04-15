from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, set_rls_user
from app.dependencies.auth import get_current_user
from app.models import AuditEventType, User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MFASetupResponse,
    MFAVerifyRequest,
    RegisterRequest,
    RegisterResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
)
from app.services import auth_service
from app.services.audit_service import audit_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await auth_service.register_user(db, body.email, body.password)
        await audit_service.record(
            db=db,
            event_type=AuditEventType.USER_REGISTERED,
            actor_id=user.id,
            payload={"email": user.email},
        )
        await db.commit()
        await db.refresh(user)
        return user
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await auth_service.login_user(
            db, body.email, body.password, body.totp_code
        )
    except ValueError as exc:
        await audit_service.record(
            db=db,
            event_type=AuditEventType.USER_LOGIN_FAILED,
            payload={"email": body.email, "reason": str(exc)},
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )

    if result.get("mfa_required"):
        await db.commit()
        return LoginResponse(mfa_required=True, access_token="", token_type="bearer")

    await audit_service.record(
        db=db,
        event_type=AuditEventType.USER_LOGIN,
        actor_id=result["user"].id,
        payload={"email": body.email},
    )
    await db.commit()

    return LoginResponse(
        access_token=result["access_token"],
        token_type="bearer",
        mfa_required=False,
        refresh_token=result["refresh_token"],
    )


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def mfa_setup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))
    data = await auth_service.setup_mfa(db, current_user)
    await db.commit()
    return MFASetupResponse(totp_uri=data["totp_uri"], qr_code_base64=data["qr_code_base64"])


@router.post("/mfa/verify")
async def mfa_verify(
    body: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))
    success = await auth_service.verify_mfa(db, current_user, body.totp_code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code"
        )
    await audit_service.record(
        db=db,
        event_type=AuditEventType.USER_MFA_ENABLED,
        actor_id=current_user.id,
        payload={"email": current_user.email},
    )
    await db.commit()
    return {"mfa_enabled": True}


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(body: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        access_token = await auth_service.refresh_access_token(db, body.refresh_token)
        return TokenRefreshResponse(access_token=access_token, token_type="bearer")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await set_rls_user(db, str(current_user.id))
    await auth_service.revoke_refresh_tokens(db, current_user.id)
    await audit_service.record(
        db=db,
        event_type=AuditEventType.USER_LOGOUT,
        actor_id=current_user.id,
        payload={"email": current_user.email},
    )
    await db.commit()
    return {"message": "logged out"}
