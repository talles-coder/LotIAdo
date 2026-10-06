"""Documento domain model."""
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel


class Documento(BaseModel):
    """Documento (memorial, contrato, tabela de preços etc.) de um tenant.

    `loteamento_id` e `lote_id` são opcionais e independentes: um documento
    pode não estar vinculado a nenhum dos dois (ex.: contrato-modelo do
    tenant), a só um loteamento, ou a um lote específico.
    """

    __tablename__ = "documentos"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    loteamento_id = Column(UUID(as_uuid=True), ForeignKey("loteamentos.id"), nullable=True)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes.id"), nullable=True)
    nome = Column(String(255), nullable=False)
    tipo = Column(String(100), nullable=True)
    content_type = Column(String(100), nullable=False)
    tamanho_bytes = Column(Integer, nullable=False)
    # Chave do objeto no bucket MinIO (não a URL — assinada sob demanda, ver
    # application/documento_service.py).
    storage_key = Column(String(512), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant")
    loteamento = relationship("Loteamento")
    lote = relationship("Lote")
