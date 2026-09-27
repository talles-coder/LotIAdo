"""Pydantic schemas for the ai_agents module's HTTP interface."""
from pydantic import BaseModel, Field


class PerguntarAgenteRequest(BaseModel):
    pergunta: str = Field(min_length=1)


class PerguntarAgenteResponse(BaseModel):
    resposta: str
