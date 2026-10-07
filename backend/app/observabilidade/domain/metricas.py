"""Métricas agregadas de chamadas de IA (FASE10-IMPL-02/SCRUM-110)."""
from dataclasses import dataclass, field


@dataclass
class MetricasPorOrigem:
    origem: str
    total_chamadas: int
    chamadas_com_erro: int
    latencia_media_ms: float | None


@dataclass
class MetricasIA:
    total_chamadas: int
    chamadas_com_erro: int
    taxa_erro: float
    latencia_media_ms: float | None
    por_origem: list[MetricasPorOrigem] = field(default_factory=list)
