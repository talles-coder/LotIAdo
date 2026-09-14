"""Authentication use cases."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.identity.application.security import (
    create_access_token,
    verify_password,
)
from app.identity.domain.exceptions import InvalidCredentialsError
from app.identity.domain.models import User
from app.identity.infrastructure.repository import (
    get_membership_for_user,
    get_user_by_email,
)


class AuthService:
    """Orchestrates login and token issuance for the identity module."""

    def __init__(self, db: AsyncSession, settings: Settings):
        self.db = db
        self.settings = settings

    async def login(self, email: str, password: str) -> str:
        """Authenticate a user by email/password and return a signed JWT."""
        user = await get_user_by_email(self.db, email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()

        membership = await get_membership_for_user(self.db, user.id)
        tenant_id = membership.tenant_id if membership else None
        return create_access_token(user.id, tenant_id, self.settings)

    async def get_current_user_with_tenant(
        self, user: User
    ) -> tuple[User, UUID | None]:
        """Return the user and their current tenant id."""
        membership = await get_membership_for_user(self.db, user.id)
        tenant_id = membership.tenant_id if membership else None
        return user, tenant_id
