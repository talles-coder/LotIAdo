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
from app.identity.infrastructure.repository import get_user_by_id

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
