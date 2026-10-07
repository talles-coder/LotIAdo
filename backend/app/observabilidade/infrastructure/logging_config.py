"""Configuração do logger `app.ia`: uma linha JSON por registro (FASE10-EST-01).

`logging` padrão configurado para saída JSON, em vez de `structlog` — evita
adicionar uma dependência nova só para um único logger com um formato de saída
fixo (ver decisão de estudo em `docs/backlog/fase-10-observabilidade-evaluation.md`).
"""
import json
import logging
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Serializa cada `LogRecord` como uma linha JSON.

    `record.msg` é o `dict` de campos estruturados passado por quem loga (ver
    `app.observabilidade.infrastructure.llm_logging`); se vier uma string comum
    (uso genérico do logger), cai em `{"message": ...}`.
    """

    def format(self, record: logging.LogRecord) -> str:
        campos = record.msg if isinstance(record.msg, dict) else {"message": record.getMessage()}
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            **campos,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configurar_logging_estruturado() -> None:
    """Liga a saída JSON no logger `app.ia`. Chamado uma vez em `app.main` na subida da aplicação."""
    logger = logging.getLogger("app.ia")
    if logger.handlers:
        return  # idempotente — evita handler duplicado sob reload do uvicorn ou testes que reimportam `app.main`
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
