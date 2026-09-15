"""FastAPI dependency that scopes a DB session to the authenticated tenant.

Ativa a Row-Level Security das tabelas de domínio (FASE2-IMPL-01): sem isso,
`app.tenant_id` nunca é setado na sessão e as policies de RLS derrubam toda
query para zero linhas (fail-closed), inclusive as do próprio tenant dono
dos dados.
"""
from uuid import UUID

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.identity.interface.dependencies import get_current_tenant_id


async def get_tenant_scoped_db(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """Yield the request's DB session with `app.tenant_id` set for the transaction.

    Usa `set_config('app.tenant_id', ..., true)` em vez de `SET LOCAL
    app.tenant_id = ...` porque `SET` não aceita parâmetros ligados
    (bind parameters) — `set_config` com `is_local=true` tem o mesmo efeito
    (escopo de transação), que é o correto com pool de conexões reaproveitadas
    entre requests (ver FASE2-EST-01-D2).
    """
    await db.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )
    return db
