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

_usuario_atual: ContextVar[UUID | None] = ContextVar("audit_usuario_atual", default=None)
_tenant_atual: ContextVar[UUID | None] = ContextVar("audit_tenant_atual", default=None)


def contexto_auditoria_atual() -> tuple[UUID | None, UUID | None]:
    """Retorna (usuario_id, tenant_id) do contexto atual, se houver."""
    return _usuario_atual.get(), _tenant_atual.get()


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
