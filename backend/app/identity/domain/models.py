"""Identity domain models."""
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint, UUID

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
