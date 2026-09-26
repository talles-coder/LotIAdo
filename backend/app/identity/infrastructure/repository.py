"""Database access for the identity module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.domain.models import (
    Invitation,
    Permission,
    RolePermission,
    User,
    UserTenantMembership,
)


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
    """Fetch the user's active tenant membership.

    A user may belong to a single tenant in practice during Fase 1, even
    though the schema already allows multiple memberships (see D6 decisions
    in docs/01-analise-requisitos.md). Inactive memberships (SCRUM-59) are
    never returned here: a deactivated user must not get a token scoped to
    that tenant.
    """
    result = await db.execute(
        select(UserTenantMembership).where(
            UserTenantMembership.user_id == user_id,
            UserTenantMembership.is_active.is_(True),
        )
    )
    return result.scalars().first()


async def get_membership_for_user_and_tenant(
    db: AsyncSession, user_id: UUID, tenant_id: UUID
) -> UserTenantMembership | None:
    """Fetch a user's membership for a specific tenant (active or not), or None if none exists.

    Deliberadamente não filtra `is_active`: chamadores que precisam
    distinguir "sem membership" de "membership desativada" (respostas HTTP
    diferentes — ver `require_permission` e `get_current_tenant_id`) checam
    `membership.is_active` eles mesmos.
    """
    result = await db.execute(
        select(UserTenantMembership).where(
            UserTenantMembership.user_id == user_id,
            UserTenantMembership.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_membership_by_id_and_tenant(
    db: AsyncSession, membership_id: UUID, tenant_id: UUID
) -> UserTenantMembership | None:
    """Fetch a membership by id, scoped to the tenant (regardless of active status)."""
    result = await db.execute(
        select(UserTenantMembership).where(
            UserTenantMembership.id == membership_id,
            UserTenantMembership.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def role_has_permission(db: AsyncSession, role: str, permission_key: str) -> bool:
    """Check whether a role is granted the given permission via role_permissions."""
    result = await db.execute(
        select(RolePermission.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role == role, Permission.key == permission_key)
    )
    return result.scalar_one_or_none() is not None


async def get_invitation_by_token(db: AsyncSession, token: str) -> Invitation | None:
    """Fetch a pending or used invitation by its token."""
    result = await db.execute(select(Invitation).where(Invitation.token == token))
    return result.scalar_one_or_none()


async def list_memberships_by_tenant(
    db: AsyncSession, tenant_id: UUID
) -> list[tuple[UserTenantMembership, User]]:
    """List every membership (active and inactive) of a tenant, joined with its user."""
    result = await db.execute(
        select(UserTenantMembership, User)
        .join(User, User.id == UserTenantMembership.user_id)
        .where(UserTenantMembership.tenant_id == tenant_id)
        .order_by(User.email)
    )
    return [(row.UserTenantMembership, row.User) for row in result.all()]


async def get_active_membership_for_email_and_tenant(
    db: AsyncSession, email: str, tenant_id: UUID
) -> UserTenantMembership | None:
    """Fetch the active membership of the user with this email in this tenant, if any."""
    result = await db.execute(
        select(UserTenantMembership)
        .join(User, User.id == UserTenantMembership.user_id)
        .where(
            User.email == email,
            UserTenantMembership.tenant_id == tenant_id,
            UserTenantMembership.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()
