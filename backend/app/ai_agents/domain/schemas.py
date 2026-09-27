"""Pydantic schemas de entrada/saída das tools de consulta do agente (FASE9-IMPL-01).

Este é o contrato combinado com FASE9-IMPL-02: o grafo do agente pode mockar
as tools a partir destes schemas enquanto é desenvolvido em paralelo. Toda
tool "não encontrado" retorna `encontrado=False` + `mensagem` em vez de
propagar exceção — o agente informa que não achou o dado, não inventa.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.vendas_reservas.domain.models import StatusReservaVenda, TipoReservaVenda


class LoteResumo(BaseModel):
    id: UUID
    loteamento_id: UUID
    identificacao: str
    quadra: str | None = None
    area_m2: Decimal | None = None
    preco: Decimal | None = None
    status: LoteStatus
    caracteristicas: dict

    model_config = {"from_attributes": True}


# --- consultar_lote ---
class ConsultarLoteInput(BaseModel):
    lote_id: UUID


class ConsultarLoteOutput(BaseModel):
    encontrado: bool
    lote: LoteResumo | None = None
    mensagem: str | None = None


# --- buscar_lotes ---
class BuscarLotesInput(BaseModel):
    loteamento_id: UUID
    status: LoteStatus | None = None
    area_m2_min: Decimal | None = None
    preco_max: Decimal | None = None


class BuscarLotesOutput(BaseModel):
    total: int
    lotes: list[LoteResumo]


# --- consultar_disponibilidade ---
class ConsultarDisponibilidadeInput(BaseModel):
    lote_id: UUID


class ConsultarDisponibilidadeOutput(BaseModel):
    encontrado: bool
    status: LoteStatus | None = None
    disponivel: bool | None = None
    mensagem: str | None = None


# --- lotes_de_esquina / lotes_proximos_de / lotes_dentro_de (geo) ---
class LotesDeEsquinaInput(BaseModel):
    loteamento_id: UUID
    status: LoteStatus | None = None
    area_m2_min: Decimal | None = None


class LotesProximosDeInput(BaseModel):
    feicao_id: UUID
    raio_m: float
    status: LoteStatus | None = None
    area_m2_min: Decimal | None = None


class LotesDentroDeInput(BaseModel):
    area_geojson: dict
    loteamento_id: UUID | None = None
    status: LoteStatus | None = None
    area_m2_min: Decimal | None = None


class LotesGeoOutput(BaseModel):
    encontrado: bool
    total: int = 0
    lotes: list[LoteResumo] = []
    mensagem: str | None = None


# --- distancia_entre_lotes (geo) ---
class DistanciaEntreLotesInput(BaseModel):
    lote_a_id: UUID
    lote_b_id: UUID


class DistanciaEntreLotesOutput(BaseModel):
    encontrado: bool
    distancia_m: float | None = None
    mensagem: str | None = None


# --- consultar_clientes ---
class ClienteResumo(BaseModel):
    id: UUID
    nome: str
    documento: str
    contato: str

    model_config = {"from_attributes": True}


class ConsultarClientesInput(BaseModel):
    cliente_id: UUID | None = None


class ConsultarClientesOutput(BaseModel):
    encontrado: bool
    total: int = 0
    clientes: list[ClienteResumo] = []
    mensagem: str | None = None


# --- consultar_corretores ---
class CorretorResumo(BaseModel):
    id: UUID
    nome: str
    contato: str

    model_config = {"from_attributes": True}


class ConsultarCorretoresInput(BaseModel):
    corretor_id: UUID | None = None


class ConsultarCorretoresOutput(BaseModel):
    encontrado: bool
    total: int = 0
    corretores: list[CorretorResumo] = []
    mensagem: str | None = None


# --- consultar_vendas ---
class ReservaResumo(BaseModel):
    id: UUID
    lote_id: UUID
    cliente_id: UUID
    corretor_id: UUID | None = None
    tipo: TipoReservaVenda
    status: StatusReservaVenda
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsultarVendasInput(BaseModel):
    reserva_id: UUID | None = None
    lote_id: UUID | None = None


class ConsultarVendasOutput(BaseModel):
    encontrado: bool
    reserva: ReservaResumo | None = None
    mensagem: str | None = None


# --- buscar_documentos (RAG) ---
class ChunkResumo(BaseModel):
    documento_id: UUID
    documento_nome: str
    texto: str
    score: float


class BuscarDocumentosInput(BaseModel):
    pergunta: str
    loteamento_id: UUID | None = None
    lote_id: UUID | None = None
    top_k: int = 5


class BuscarDocumentosOutput(BaseModel):
    encontrado: bool
    resultados: list[ChunkResumo] = []
    mensagem: str | None = None


# --- consultar_condicoes_comerciais ---
class ConsultarCondicoesComerciaisInput(BaseModel):
    lote_id: UUID


class ConsultarCondicoesComerciaisOutput(BaseModel):
    encontrado: bool
    preco: Decimal | None = None
    area_m2: Decimal | None = None
    caracteristicas: dict | None = None
    mensagem: str | None = None
