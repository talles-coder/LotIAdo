"""Identity module HTTP routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import get_db
from app.identity.application.auth_service import AuthService
from app.identity.domain.exceptions import InvalidCredentialsError
from app.identity.domain.models import User
from app.identity.interface.dependencies import get_current_user, get_settings
from app.identity.interface.schemas import LoginRequest, LoginResponse, UserMeResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> LoginResponse:
    """Authenticate with email/password and receive a JWT access token."""
    service = AuthService(db, settings)
    try:
        token = await service.login(request.email, request.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return LoginResponse(access_token=token)


@router.get("/me", response_model=UserMeResponse)
async def me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UserMeResponse:
    """Return the authenticated user and their current tenant."""
    service = AuthService(db, settings)
    user, tenant_id = await service.get_current_user_with_tenant(current_user)
    return UserMeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        tenant_id=tenant_id,
    )
