"""Helper reutilizável de auditoria.

Ponto de sincronização combinado em docs/backlog/fase-1-mvp-dominio.md
(FASE1-IMPL-04): os demais módulos (loteamentos_lotes, vendas_reservas, ...)
chamam `registrar_auditoria(...)` uma única vez, ao final de uma ação
sensível no service, em vez de reimplementar a gravação do log. Isso mantém
a lógica de auditoria centralizada num único lugar, em vez de duplicada
rota a rota.
"""
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.domain.models import AuditLog
from app.audit.infrastructure.repository import create


async def registrar_auditoria(
    db: AsyncSession,
    *,
    tenant_id: UUID,
    usuario_id: UUID,
    acao: str,
    entidade: str,
    entidade_id: UUID,
    payload_antes: dict[str, Any] | None = None,
    payload_depois: dict[str, Any] | None = None,
) -> AuditLog:
    """Registra uma entrada de auditoria para uma ação sensível.

    Chamar a partir do service do módulo responsável, após a ação de negócio
    ter sido persistida (ex.: ao final de `LoteService.transicionar_status`
    ou `ReservaService.criar`), usando `acao` de `AcaoAuditoria` sempre que
    aplicável.
    """
    audit_log = AuditLog(
        tenant_id=tenant_id,
        usuario_id=usuario_id,
        acao=str(acao),
        entidade=entidade,
        entidade_id=entidade_id,
        payload_antes=payload_antes,
        payload_depois=payload_depois,
    )
    return await create(db, audit_log)
