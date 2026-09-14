"""Pydantic schemas for the corretores module's HTTP interface."""
from uuid import UUID

from pydantic import BaseModel


class CorretorCreateRequest(BaseModel):
    nome: str
    contato: str
    usuario_id: UUID | None = None


class CorretorUpdateRequest(BaseModel):
    nome: str | None = None
    contato: str | None = None
    usuario_id: UUID | None = None


class CorretorResponse(BaseModel):
    id: UUID
    nome: str
    contato: str
    usuario_id: UUID | None

    model_config = {"from_attributes": True}
