"""Pydantic schemas for the ai_rag module's HTTP interface."""
from uuid import UUID

from pydantic import BaseModel, Field

from app.ai_rag.application.busca_service import TOP_K_PADRAO


class BuscaSemanticaRequest(BaseModel):
    pergunta: str = Field(min_length=1)
    loteamento_id: UUID | None = None
    lote_id: UUID | None = None
    top_k: int = Field(default=TOP_K_PADRAO, ge=1, le=20)


class ChunkResultado(BaseModel):
    chunk_id: UUID
    documento_id: UUID
    documento_nome: str
    texto: str
    ordem: int
    score: float

    model_config = {"from_attributes": True}


class PerguntaRequest(BaseModel):
    pergunta: str = Field(min_length=1)
    loteamento_id: UUID | None = None
    lote_id: UUID | None = None
    top_k: int = Field(default=TOP_K_PADRAO, ge=1, le=20)


class FonteResposta(BaseModel):
    documento_id: UUID
    documento_nome: str
    trecho: str

    model_config = {"from_attributes": True}


class PerguntaResponse(BaseModel):
    resposta: str
    fontes: list[FonteResposta]

    model_config = {"from_attributes": True}
