"""Pydantic schemas for the ai_agents module's HTTP interface."""
from uuid import UUID

from pydantic import BaseModel, Field


class PerguntarAgenteRequest(BaseModel):
    pergunta: str = Field(min_length=1)


class ConfirmacaoAcaoPendente(BaseModel):
    """Card de confirmação: proposta de ação sensível esperando aprovação/recusa do usuário."""

    confirmacao_id: UUID
    tool: str
    descricao: str
    argumentos: dict


class PerguntarAgenteResponse(BaseModel):
    """Exatamente um de `resposta`/`confirmacao` vem preenchido por chamada.

    `resposta=None` + `confirmacao` presente significa que o agente propôs
    uma ação sensível e está pausado aguardando `POST /agente/confirmar`.
    """

    resposta: str | None = None
    confirmacao: ConfirmacaoAcaoPendente | None = None


class ConfirmarAcaoRequest(BaseModel):
    confirmacao_id: UUID
    aprovado: bool
