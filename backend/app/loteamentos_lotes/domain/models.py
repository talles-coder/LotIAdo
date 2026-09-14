"""Loteamento e Lote domain models."""
from sqlalchemy import Column, DateTime, ForeignKey, JSON, Numeric, String, UUID
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.loteamentos_lotes.domain.state_machine import LoteStatus


class Loteamento(BaseModel):
    """Loteamento (empreendimento) cadastrado por um tenant, contendo lotes."""

    __tablename__ = "loteamentos"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    nome = Column(String(255), nullable=False)
    descricao = Column(String(1000), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")


class Lote(BaseModel):
    """Lote pertencente a um loteamento, com status controlado por máquina de estados."""

    __tablename__ = "lotes"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    loteamento_id = Column(UUID(as_uuid=True), ForeignKey("loteamentos.id"), nullable=False)
    identificacao = Column(String(50), nullable=False)
    quadra = Column(String(50), nullable=True)
    area_m2 = Column(Numeric(10, 2), nullable=True)
    preco = Column(Numeric(12, 2), nullable=True)
    status = Column(
        SAEnum(
            LoteStatus,
            name="lote_status",
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        nullable=False,
        default=LoteStatus.DISPONIVEL,
    )
    caracteristicas = Column(JSON, nullable=True, default=dict)
    corretor_id = Column(UUID(as_uuid=True), ForeignKey("corretores.id"), nullable=True)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
    loteamento = relationship("Loteamento")
