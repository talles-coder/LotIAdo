"""Pydantic schemas for the loteamentos_lotes module's HTTP interface."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.loteamentos_lotes.domain.state_machine import LoteStatus


class LoteamentoCreateRequest(BaseModel):
    nome: str
    descricao: str | None = None


class LoteamentoUpdateRequest(BaseModel):
    nome: str | None = None
    descricao: str | None = None


class LoteamentoResponse(BaseModel):
    id: UUID
    nome: str
    descricao: str | None

    model_config = {"from_attributes": True}


class LoteCreateRequest(BaseModel):
    identificacao: str
    quadra: str | None = None
    area_m2: Decimal | None = None
    preco: Decimal | None = None
    caracteristicas: dict | None = None


class LoteUpdateRequest(BaseModel):
    quadra: str | None = None
    area_m2: Decimal | None = None
    preco: Decimal | None = None
    caracteristicas: dict | None = None
    corretor_id: UUID | None = None
    cliente_id: UUID | None = None


class LoteStatusUpdateRequest(BaseModel):
    status: LoteStatus


class LoteResponse(BaseModel):
    id: UUID
    loteamento_id: UUID
    identificacao: str
    quadra: str | None
    area_m2: Decimal | None
    preco: Decimal | None
    status: LoteStatus
    caracteristicas: dict | None
    corretor_id: UUID | None
    cliente_id: UUID | None

    model_config = {"from_attributes": True}


class ImportacaoCsvPreviewResponse(BaseModel):
    colunas: list[str]


class ImportacaoErroLinha(BaseModel):
    linha: int
    erro: str


class ImportacaoLoteResponse(BaseModel):
    total_linhas: int
    importados: int
    erros: list[ImportacaoErroLinha]
