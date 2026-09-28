"""DocumentChunk domain model."""
from sqlalchemy import Column, ForeignKey, Integer, Text, UUID
from sqlalchemy.orm import relationship

from app.common.models import BaseModel
from app.config import Settings
from pgvector.sqlalchemy import Vector

_EMBEDDING_DIMENSIONS = Settings().embedding_dimensions


class DocumentChunk(BaseModel):
    """Um chunk de texto de um documento, com seu embedding e metadados de escopo.

    `tenant_id`/`loteamento_id`/`lote_id` são herdados do `Documento` de
    origem e duplicados aqui (em vez de só via join) porque toda busca
    vetorial (FASE7-IMPL-03) filtra por eles diretamente na mesma query —
    defesa em profundidade além da RLS, conforme CLAUDE.md.
    """

    __tablename__ = "document_chunks"

    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    loteamento_id = Column(UUID(as_uuid=True), ForeignKey("loteamentos.id"), nullable=True)
    lote_id = Column(UUID(as_uuid=True), ForeignKey("lotes.id"), nullable=True)
    ordem = Column(Integer, nullable=False)
    texto = Column(Text, nullable=False)
    embedding = Column(Vector(_EMBEDDING_DIMENSIONS), nullable=False)

    documento = relationship("Documento")
    tenant = relationship("Tenant")
    loteamento = relationship("Loteamento")
    lote = relationship("Lote")
