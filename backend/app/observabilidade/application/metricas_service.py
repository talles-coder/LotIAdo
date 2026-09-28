"""Agrega os eventos do log estruturado de IA (FASE10-IMPL-01) em métricas simples (FASE10-IMPL-02).

Lê `logs/app-ia.jsonl` direto do disco — sem banco, sem Prometheus/Grafana
(decisão explícita da task: volume de portfólio não justifica a complexidade).
Só o arquivo atual do `RotatingFileHandler` é lido (não os backups rotacionados);
adequado ao volume esperado.
"""
import json
from pathlib import Path

from app.observabilidade.domain.metricas import MetricasIA, MetricasPorOrigem
from app.observabilidade.infrastructure.logging_config import CAMINHO_LOG_IA


class MetricasIAService:
    def __init__(self, caminho_log: Path | None = None):
        # Lookup do módulo em tempo de chamada (não default de argumento, fixo
        # em tempo de import) — permite testar com `monkeypatch.setattr(
        # "app.observabilidade.application.metricas_service.CAMINHO_LOG_IA", ...)`.
        self.caminho_log = caminho_log if caminho_log is not None else CAMINHO_LOG_IA

    def obter_metricas(self) -> MetricasIA:
        eventos = list(_ler_eventos(self.caminho_log))
        return _agregar(eventos)


def _ler_eventos(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    eventos = []
    with caminho.open("r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if not linha:
                continue
            try:
                evento = json.loads(linha)
            except json.JSONDecodeError:
                continue  # linha truncada (ex.: escrita concorrente) — ignora, não quebra a agregação
            if "sucesso" in evento and "latencia_ms" in evento:
                eventos.append(evento)
    return eventos


def _agregar(eventos: list[dict]) -> MetricasIA:
    total = len(eventos)
    com_erro = sum(1 for evento in eventos if not evento.get("sucesso", True))
    latencia_media = _media([evento["latencia_ms"] for evento in eventos]) if total else None

    origens = sorted({evento.get("origem", "desconhecida") for evento in eventos})
    por_origem = [
        _agregar_origem(origem, [evento for evento in eventos if evento.get("origem", "desconhecida") == origem])
        for origem in origens
    ]

    return MetricasIA(
        total_chamadas=total,
        chamadas_com_erro=com_erro,
        taxa_erro=(com_erro / total) if total else 0.0,
        latencia_media_ms=latencia_media,
        por_origem=por_origem,
    )


def _agregar_origem(origem: str, eventos: list[dict]) -> MetricasPorOrigem:
    total = len(eventos)
    com_erro = sum(1 for evento in eventos if not evento.get("sucesso", True))
    return MetricasPorOrigem(
        origem=origem,
        total_chamadas=total,
        chamadas_com_erro=com_erro,
        latencia_media_ms=_media([evento["latencia_ms"] for evento in eventos]) if total else None,
    )


def _media(valores: list[float]) -> float:
    return round(sum(valores) / len(valores), 1)
