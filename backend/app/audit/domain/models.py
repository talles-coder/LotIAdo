"""Audit log domain model."""
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UUID, func
from sqlalchemy.orm import relationship

from app.common.models import Base


class AuditLog(Base):
    """Entrada imutável de auditoria de uma ação sensível.

    Append-only por convenção: o módulo audit não expõe nenhuma função de
    update/delete (ver `app.audit.infrastructure.repository`), então não há
    como uma entrada já persistida ser alterada ou removida pela aplicação.
    Por isso o modelo não herda de `BaseModel` (que traz `updated_at`).
    """

    __tablename__ = "audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    acao = Column(String(100), nullable=False)
    entidade = Column(String(100), nullable=False)
    entidade_id = Column(UUID(as_uuid=True), nullable=False)
    payload_antes = Column(JSON, nullable=True)
    payload_depois = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship("Tenant")
    usuario = relationship("User")
