"""Identity domain models."""
from sqlalchemy import Boolean, Column, DateTime, String, ForeignKey, UniqueConstraint, UUID

from app.common.models import BaseModel


class User(BaseModel):
    """User account, independent of any tenant."""

    __tablename__ = "users"

    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)


class UserTenantMembership(BaseModel):
    """Association between a user and a tenant, with a role."""

    __tablename__ = "user_tenant_membership"
    __table_args__ = (
        UniqueConstraint("user_id", "tenant_id", name="uq_user_tenant_membership"),
    )

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    role = Column(String(50), nullable=False, default="member")
    is_active = Column(Boolean, nullable=False, default=True)


class Permission(BaseModel):
    """A single grantable permission, identified by a stable key."""

    __tablename__ = "permissions"

    key = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=False)


class RolePermission(BaseModel):
    """Grants a permission to every membership with the given role."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role", "permission_id", name="uq_role_permissions"),
    )

    role = Column(String(50), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)


class Invitation(BaseModel):
    """A single-use, time-limited invitation for someone to join a tenant.

    Fica fora da RLS, como `users`/`tenants`/`user_tenant_membership` (ver
    TENANT_CONVENTION.md): o aceite acontece antes de existir qualquer sessão
    de tenant autenticada.
    """

    __tablename__ = "invitations"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
