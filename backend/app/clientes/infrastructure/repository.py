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
    """Persist a new cliente."""
    db.add(cliente)
    await db.commit()
    await db.refresh(cliente)
    return cliente


async def save(db: AsyncSession, cliente: Cliente) -> Cliente:
    """Persist changes made to an existing cliente."""
    await db.commit()
    await db.refresh(cliente)
    return cliente
