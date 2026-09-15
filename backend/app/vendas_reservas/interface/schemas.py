"""Pydantic schemas for the vendas_reservas module's HTTP interface."""
from uuid import UUID

from pydantic import BaseModel

from app.vendas_reservas.domain.models import StatusReservaVenda, TipoReservaVenda


class ReservaCreateRequest(BaseModel):
    lote_id: UUID
    cliente_id: UUID
    corretor_id: UUID | None = None


class ReservaResponse(BaseModel):
    id: UUID
    lote_id: UUID
    cliente_id: UUID
    corretor_id: UUID | None
    tipo: TipoReservaVenda
    status: StatusReservaVenda

    model_config = {"from_attributes": True}
