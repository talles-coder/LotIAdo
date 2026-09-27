"""Fila RQ (Redis) usada para processar documentos de forma assíncrona.

Uma conexão/fila por chamada (em vez de um singleton no import do módulo,
como `app.ai_rag.llm_provider`) porque `redis.Redis` não é thread/process
-safe compartilhado entre o processo da API e o override de testes — cada
enfileiramento abre e fecha sua própria conexão, que é barata para uso local.
"""
from uuid import UUID

import redis
from rq import Queue

from app.config import Settings

NOME_FILA = "documentos"


def _fila(settings: Settings) -> Queue:
    conexao = redis.from_url(settings.redis_url)
    return Queue(NOME_FILA, connection=conexao)


def enfileirar_processamento_documento(documento_id: UUID, tenant_id: UUID, settings: Settings) -> None:
    """Enfileira o job `processar_documento(documento_id, tenant_id)` (FASE7-IMPL-01)."""
    _fila(settings).enqueue(
        "app.ai_rag.application.ingestao_service.processar_documento",
        str(documento_id),
        str(tenant_id),
    )
