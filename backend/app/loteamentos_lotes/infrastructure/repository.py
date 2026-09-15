"""Database access for the loteamentos_lotes module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.loteamentos_lotes.domain.models import Loteamento, Lote


async def get_loteamento_by_id(
    db: AsyncSession, tenant_id: UUID, loteamento_id: UUID
) -> Loteamento | None:
    """Fetch an active (non-removed) loteamento by id, scoped to the tenant."""
    result = await db.execute(
        select(Loteamento).where(
            Loteamento.id == loteamento_id,
            Loteamento.tenant_id == tenant_id,
            Loteamento.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_loteamentos_by_tenant(db: AsyncSession, tenant_id: UUID) -> list[Loteamento]:
    """List all active (non-removed) loteamentos for the tenant."""
    result = await db.execute(
        select(Loteamento).where(
            Loteamento.tenant_id == tenant_id,
            Loteamento.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def create_loteamento(db: AsyncSession, loteamento: Loteamento) -> Loteamento:
    """Persist a new loteamento."""
    db.add(loteamento)
    await db.commit()
    await db.refresh(loteamento)
    return loteamento


async def save_loteamento(db: AsyncSession, loteamento: Loteamento) -> Loteamento:
    """Persist changes made to an existing loteamento."""
    await db.commit()
    await db.refresh(loteamento)
    return loteamento


async def get_lote_by_id(db: AsyncSession, tenant_id: UUID, lote_id: UUID) -> Lote | None:
    """Fetch an active (non-removed) lote by id, scoped to the tenant."""
    result = await db.execute(
        select(Lote).where(
            Lote.id == lote_id,
            Lote.tenant_id == tenant_id,
            Lote.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def get_lote_by_id_for_update(db: AsyncSession, tenant_id: UUID, lote_id: UUID) -> Lote | None:
    """Fetch an active lote locking its row (`SELECT ... FOR UPDATE`) until the transaction ends.

    Used before a status transition that must not race with a concurrent one
    (ex.: duas reservas simultâneas do mesmo lote em `vendas_reservas`) — o
    segundo `SELECT FOR UPDATE` bloqueia até a primeira transação commitar,
    e então enxerga o status já atualizado.
    """
    result = await db.execute(
        select(Lote)
        .where(
            Lote.id == lote_id,
            Lote.tenant_id == tenant_id,
            Lote.deleted_at.is_(None),
        )
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def list_lotes_by_loteamento(
    db: AsyncSession, tenant_id: UUID, loteamento_id: UUID
) -> list[Lote]:
    """List all active (non-removed) lotes for a loteamento, scoped to the tenant."""
    result = await db.execute(
        select(Lote).where(
            Lote.tenant_id == tenant_id,
            Lote.loteamento_id == loteamento_id,
            Lote.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def create_lote(db: AsyncSession, lote: Lote) -> Lote:
    """Persist a new lote."""
    db.add(lote)
    await db.commit()
    await db.refresh(lote)
    return lote


async def save_lote(db: AsyncSession, lote: Lote) -> Lote:
    """Persist changes made to an existing lote."""
    await db.commit()
    await db.refresh(lote)
    return lote
