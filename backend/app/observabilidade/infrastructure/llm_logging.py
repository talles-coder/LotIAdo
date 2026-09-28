"""Wrapper de instrumentação para toda chamada ao `LLMProvider` (FASE10-IMPL-01/SCRUM-109).

Usado dentro de `OllamaLLMProvider.embed/generate/chat`: cronometra a chamada,
registra sucesso/erro e loga um evento estruturado no logger `app.ia`,
correlacionado por `request_id` (da request HTTP atual) e `origem` (rag/agente/
importação, marcada pelo caller via `contexto_origem_ia`).
"""
import logging
import time
from contextlib import contextmanager
from typing import Iterator
from uuid import uuid4

from app.observabilidade.domain.chamada_ia import OrigemChamadaIA
from app.observabilidade.infrastructure.context import origem_ia_atual, request_id_atual

logger = logging.getLogger("app.ia")


@contextmanager
def medir_chamada_llm(*, metodo: str, modelo: str) -> Iterator[dict]:
    """Cronometra e loga uma chamada ao `LLMProvider`.

    Devolve um `dict` mutável (`tokens_entrada`/`tokens_saida`, ambos `None` por
    padrão) para o chamador preencher quando o provider expuser essa contagem —
    hoje só `/api/generate` e `/api/chat` do Ollama devolvem, `/api/embeddings` não.
    Relança qualquer exceção da chamada real após logar `sucesso=False`.
    """
    resultado: dict = {"tokens_entrada": None, "tokens_saida": None}
    inicio = time.perf_counter()
    erro: str | None = None
    try:
        yield resultado
    except Exception as exc:
        erro = str(exc)
        raise
    finally:
        latencia_ms = round((time.perf_counter() - inicio) * 1000, 1)
        origem = origem_ia_atual() or OrigemChamadaIA.DESCONHECIDA
        payload = {
            "request_id": request_id_atual() or str(uuid4()),
            "origem": origem.value,
            "metodo": metodo,
            "modelo": modelo,
            "latencia_ms": latencia_ms,
            "tokens_entrada": resultado["tokens_entrada"],
            "tokens_saida": resultado["tokens_saida"],
            "sucesso": erro is None,
        }
        if erro is not None:
            payload["erro"] = erro
        logger.info(payload)
