"""Database access for the clientes module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clientes.domain.models import Cliente


async def get_by_id(db: AsyncSession, tenant_id: UUID, cliente_id: UUID) -> Cliente | None:
    """Fetch an active (non-removed) cliente by id, scoped to the tenant."""
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.tenant_id == tenant_id,
            Cliente.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_by_tenant(db: AsyncSession, tenant_id: UUID) -> list[Cliente]:
    """List all active (non-removed) clientes for the tenant."""
    result = await db.execute(
        select(Cliente).where(
            Cliente.tenant_id == tenant_id,
            Cliente.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, cliente: Cliente) -> Cliente:
    """Persist a new cliente.

    Sem `db.refresh()` de propósito: a sessão tem `expire_on_commit=False`
    (ver app/database.py) e o INSERT já traz os defaults gerados pelo server
    (`created_at`/`updated_at`) via `RETURNING`, então o objeto já está
    completo após o commit. Um `refresh()` abriria uma *nova* transação sem
    `app.tenant_id` setado — a policy de RLS derrubaria a query pra zero
    linhas (ver app/tenancy/interface/dependencies.py).
    """
    db.add(cliente)
    await db.commit()
    return cliente


async def save(db: AsyncSession, cliente: Cliente) -> Cliente:
    """Persist changes made to an existing cliente. Ver nota em `create()`."""
    await db.commit()
    return cliente
