"""Contexto de auditoria (usuário/tenant atual), acessível fora da request.

O listener de auditoria automática (`app.audit.infrastructure.tracking`) roda
em nível de SQLAlchemy `Session`, sem acesso direto ao objeto `Request` do
FastAPI. Por isso quem está autenticado na request atual fica disponível
aqui via `contextvars`, preenchido uma única vez por request pelo
`AuditContextMiddleware` — nenhuma rota ou service precisa propagar isso
manualmente.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator
from uuid import UUID

from app.audit.domain.acoes import OrigemAuditoria

_usuario_atual: ContextVar[UUID | None] = ContextVar("audit_usuario_atual", default=None)
_tenant_atual: ContextVar[UUID | None] = ContextVar("audit_tenant_atual", default=None)
_origem_atual: ContextVar[OrigemAuditoria] = ContextVar("audit_origem_atual", default=OrigemAuditoria.USUARIO)


def contexto_auditoria_atual() -> tuple[UUID | None, UUID | None]:
    """Retorna (usuario_id, tenant_id) do contexto atual, se houver."""
    return _usuario_atual.get(), _tenant_atual.get()


def origem_auditoria_atual() -> OrigemAuditoria:
    """Retorna a origem (usuário direto ou agente de IA) da mudança atual."""
    return _origem_atual.get()


@contextmanager
def contexto_auditoria(*, usuario_id: UUID, tenant_id: UUID) -> Iterator[None]:
    """Define o usuário/tenant atual para auditoria automática neste escopo.

    Usado pelo `AuditContextMiddleware` a cada request e, fora de uma request
    HTTP (scripts, jobs, testes), por qualquer código que precise fazer
    alterações em entidades rastreadas.
    """
    token_usuario = _usuario_atual.set(usuario_id)
    token_tenant = _tenant_atual.set(tenant_id)
    try:
        yield
    finally:
        _usuario_atual.reset(token_usuario)
        _tenant_atual.reset(token_tenant)


@contextmanager
def contexto_origem_auditoria(origem: OrigemAuditoria) -> Iterator[None]:
    """Marca a origem da mudança feita neste escopo (dentro de um `contexto_auditoria` já ativo).

    Usado pelo agente de IA (FASE9-IMPL-03) ao executar, após confirmação
    humana, uma tool de ação: `usuario_id`/`tenant_id` continuam sendo os de
    quem confirmou (já populados pelo `AuditContextMiddleware`), só a origem
    muda — é isso que distingue, no `audit_log`, uma ação feita direto na
    tela de uma proposta pelo agente e aprovada.
    """
    token = _origem_atual.set(origem)
    try:
        yield
    finally:
        _origem_atual.reset(token)
