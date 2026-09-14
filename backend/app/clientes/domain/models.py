"""Cliente domain model."""
from sqlalchemy import Column, DateTime, String, ForeignKey, UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel


class Cliente(BaseModel):
    """Cliente cadastrado por um tenant, referenciável por reservas/vendas."""

    __tablename__ = "clientes"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    documento = Column(String(50), nullable=False)
    contato = Column(String(255), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
