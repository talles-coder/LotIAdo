"""Pydantic schemas for the documentos module's HTTP interface."""
from uuid import UUID

from pydantic import BaseModel


class DocumentoResponse(BaseModel):
    id: UUID
    nome: str
    tipo: str | None
    content_type: str
    tamanho_bytes: int
    loteamento_id: UUID | None
    lote_id: UUID | None

    model_config = {"from_attributes": True}


class DocumentoUrlAssinadaResponse(BaseModel):
    url: str
