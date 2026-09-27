"""Fila RQ para o job de extração de imagem de planta (FASE8-IMPL-02/SCRUM-100).

Reaproveita a mesma fila `documentos` (e o mesmo worker) já introduzidos em
`app/ai_rag/infrastructure/queue.py` (FASE7-IMPL-01) — só um novo tipo de job, sem fila/worker
próprios, conforme `docs/backlog/fase-8-ia-importacao.md`.
"""
from uuid import UUID

import redis
from rq import Queue

from app.ai_rag.infrastructure.queue import NOME_FILA
from app.config import Settings


def enfileirar_extracao_imagem(documento_id: UUID, tenant_id: UUID, settings: Settings) -> None:
    """Enfileira o job `processar_extracao_imagem(documento_id, tenant_id)` (FASE8-IMPL-02)."""
    conexao = redis.from_url(settings.redis_url)
    Queue(NOME_FILA, connection=conexao).enqueue(
        "app.documentos.application.extracao_imagem_service.processar_extracao_imagem",
        str(documento_id),
        str(tenant_id),
    )
