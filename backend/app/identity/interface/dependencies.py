"""FastAPI dependencies for authenticating requests."""
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import get_db
from app.identity.application.security import decode_access_token
from app.identity.domain.models import User
from app.identity.infrastructure.repository import (
    get_membership_for_user_and_tenant,
    get_user_by_id,
    role_has_permission,
)

_bearer_scheme = HTTPBearer(auto_error=False)


def get_settings() -> Settings:
    return Settings()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Resolve the authenticated user from the request's bearer token."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials, settings)
    except jwt.PyJWTError:
        raise unauthorized

    raw_user_id = payload.get("sub")
    if raw_user_id is None:
        raise unauthorized

    try:
        user_id = UUID(raw_user_id)
    except ValueError:
        raise unauthorized

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise unauthorized

    return user


async def get_current_tenant_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> UUID:
    """Resolve the tenant id scoping the authenticated request's bearer token.

    Reconfere no banco se a membership referenciada pelo token não foi
    desativada (não confia só no claim `tenant_id` do JWT): um JWT já
    emitido continua criptograficamente válido até expirar, então sem essa
    checagem um usuário desativado (SCRUM-59) continuaria autenticado no
    tenant até o token expirar. Não rejeita quando a membership simplesmente
    não existe (nunca existiu) — esse caso já é tratado, com 403, por rotas
    que dependem de `require_permission`; aqui só o caso "existia e foi
    desativada" vira 401 (autenticação inválida), para não mudar o
    comportamento de rotas sem checagem de permissão.
    """
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = decode_access_token(credentials.credentials, settings)
    except jwt.PyJWTError:
        raise unauthorized

    raw_tenant_id = payload.get("tenant_id")
    if raw_tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no associated tenant",
        )

    try:
        tenant_id = UUID(raw_tenant_id)
    except ValueError:
        raise unauthorized

    raw_user_id = payload.get("sub")
    try:
        user_id = UUID(raw_user_id) if raw_user_id is not None else None
    except ValueError:
        user_id = None
    if user_id is None:
        raise unauthorized

    membership = await get_membership_for_user_and_tenant(db, user_id, tenant_id)
    if membership is not None and not membership.is_active:
        raise unauthorized

    return tenant_id


def require_permission(permission_key: str):
    """Build a dependency that only allows requests whose role grants `permission_key`.

    Permissions are resolved via `role_permissions`, not a hardcoded role name,
    so granting a new permission to a custom role never requires touching route code.
    """

    async def _dependency(
        user: User = Depends(get_current_user),
        tenant_id: UUID = Depends(get_current_tenant_id),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        membership = await get_membership_for_user_and_tenant(db, user.id, tenant_id)
        if membership is None or not membership.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no membership in this tenant",
            )

        if not await role_has_permission(db, membership.role, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{membership.role}' is missing permission '{permission_key}'",
            )

    return _dependency
