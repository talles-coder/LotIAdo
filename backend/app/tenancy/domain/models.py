"""Tenant domain models."""
from sqlalchemy import Column, String, JSON
from app.common.models import BaseModel


class Tenant(BaseModel):
    """Tenant entity representing a distinct organization or workspace."""

    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    config = Column(JSON, nullable=True, default={})
