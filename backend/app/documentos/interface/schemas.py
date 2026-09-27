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
    status_indexacao: str
    # Sugestão de extração de imagem (FASE8-IMPL-02/SCRUM-100): None até ser pedida (nem todo
    # documento é uma planta); depois pendente -> processando -> concluido | falhou.
    status_extracao_imagem: str | None
    resultado_extracao_imagem: dict | None

    model_config = {"from_attributes": True}


class DocumentoUrlAssinadaResponse(BaseModel):
    url: str
