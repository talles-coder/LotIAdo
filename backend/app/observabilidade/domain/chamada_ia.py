"""Origem de uma chamada ao `LLMProvider`, para correlação nos logs estruturados (FASE10-IMPL-01)."""
from enum import StrEnum


class OrigemChamadaIA(StrEnum):
    """De qual módulo partiu a chamada ao `LLMProvider`."""

    RAG = "rag"
    AGENTE = "agente"
    IMPORTACAO = "importacao"
    DESCONHECIDA = "desconhecida"
