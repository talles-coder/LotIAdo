"""Pydantic schemas for the clientes module's HTTP interface."""
from uuid import UUID

from pydantic import BaseModel


class ClienteCreateRequest(BaseModel):
    nome: str
    documento: str
    contato: str


class ClienteUpdateRequest(BaseModel):
    nome: str | None = None
    documento: str | None = None
    contato: str | None = None


class ClienteResponse(BaseModel):
    id: UUID
    nome: str
    documento: str
    contato: str

    model_config = {"from_attributes": True}
