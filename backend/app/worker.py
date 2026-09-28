"""Entrypoint do worker RQ (processo separado do backend, ver docker-compose.yml).

Roda com: `python -m app.worker` (localmente) ou como CMD do serviço `worker`
no docker-compose. Consome a fila `documentos` (app/ai_rag/infrastructure/queue.py),
processando jobs de `processar_documento` (chunking + embeddings, FASE7-IMPL-01).
"""
import redis
from rq import Queue, Worker

from app.ai_rag.infrastructure.queue import NOME_FILA
from app.config import Settings
from app.observabilidade.infrastructure.logging_config import configurar_logging_estruturado


def main() -> None:
    # Processo separado da API — `app.main` nunca roda aqui, então o log
    # estruturado das chamadas de IA feitas durante `processar_documento`
    # (embed de cada chunk, origem IMPORTACAO) precisa ser ligado de novo
    # (ver FASE10-IMPL-01/SCRUM-109).
    configurar_logging_estruturado()
    settings = Settings()
    conexao = redis.from_url(settings.redis_url)
    worker = Worker([Queue(NOME_FILA, connection=conexao)], connection=conexao)
    worker.work()


if __name__ == "__main__":
    main()
