"""Corretor domain model."""
from sqlalchemy import Column, DateTime, String, ForeignKey, UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel


class Corretor(BaseModel):
    """Corretor cadastrado por um tenant, opcionalmente associado a um usuário."""

    __tablename__ = "corretores"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    contato = Column(String(255), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
    usuario = relationship("User")
