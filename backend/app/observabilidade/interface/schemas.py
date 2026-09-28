"""Pydantic schemas for the observabilidade module's HTTP interface."""
from pydantic import BaseModel


class MetricasPorOrigemResponse(BaseModel):
    origem: str
    total_chamadas: int
    chamadas_com_erro: int
    latencia_media_ms: float | None


class MetricasIAResponse(BaseModel):
    total_chamadas: int
    chamadas_com_erro: int
    taxa_erro: float
    latencia_media_ms: float | None
    por_origem: list[MetricasPorOrigemResponse]
