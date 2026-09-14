"""Database access for the identity module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.domain.models import User, UserTenantMembership


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email, or None if no such user exists."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Fetch a user by id, or None if no such user exists."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_membership_for_user(
    db: AsyncSession, user_id: UUID
) -> UserTenantMembership | None:
    """Fetch the tenant membership for a user.

    A user may belong to a single tenant in practice during Fase 1, even
    though the schema already allows multiple memberships (see D6 decisions
    in docs/01-analise-requisitos.md).
    """
    result = await db.execute(
        select(UserTenantMembership).where(UserTenantMembership.user_id == user_id)
    )
    return result.scalars().first()
