"""Contexto de observabilidade de IA (request_id/origem), acessível fora da request.

Mesmo padrão de `app.audit.infrastructure.context`: `OllamaLLMProvider` loga uma
chamada sem saber quem a originou (rag/agente/importação) nem em qual request
HTTP ela está — por isso esse contexto fica em `contextvars`, preenchido pelo
`RequestIdMiddleware` (request_id) e por cada application service, no ponto em
que chama o `LLMProvider` (origem), sem precisar mudar a assinatura de
`LLMProvider.embed/generate/chat`.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator

from app.observabilidade.domain.chamada_ia import OrigemChamadaIA

_request_id_atual: ContextVar[str | None] = ContextVar("observabilidade_request_id_atual", default=None)
_origem_ia_atual: ContextVar[OrigemChamadaIA | None] = ContextVar("observabilidade_origem_ia_atual", default=None)


def request_id_atual() -> str | None:
    """Retorna o `request_id` da request HTTP atual, se houver (`RequestIdMiddleware`)."""
    return _request_id_atual.get()


def origem_ia_atual() -> OrigemChamadaIA | None:
    """Retorna o módulo de origem da chamada de IA em andamento, se marcado via `contexto_origem_ia`."""
    return _origem_ia_atual.get()


@contextmanager
def contexto_request_id(request_id: str) -> Iterator[None]:
    """Define o `request_id` para toda chamada de IA feita neste escopo. Usado pelo `RequestIdMiddleware`."""
    token = _request_id_atual.set(request_id)
    try:
        yield
    finally:
        _request_id_atual.reset(token)


@contextmanager
def contexto_origem_ia(origem: OrigemChamadaIA) -> Iterator[None]:
    """Marca o módulo de origem (rag/agente/importação) da(s) chamada(s) de IA feita(s) neste escopo.

    Cada application service que chama `ai_rag.llm_provider` envolve a chamada
    nesse context manager — é o que permite ao log estruturado dizer de onde
    ela veio sem acoplar `OllamaLLMProvider` a nenhum módulo chamador.
    """
    token = _origem_ia_atual.set(origem)
    try:
        yield
    finally:
        _origem_ia_atual.reset(token)
