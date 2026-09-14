"""Database access for the corretores module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.corretores.domain.models import Corretor


async def get_by_id(db: AsyncSession, tenant_id: UUID, corretor_id: UUID) -> Corretor | None:
    """Fetch an active (non-removed) corretor by id, scoped to the tenant."""
    result = await db.execute(
        select(Corretor).where(
            Corretor.id == corretor_id,
            Corretor.tenant_id == tenant_id,
            Corretor.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_by_tenant(db: AsyncSession, tenant_id: UUID) -> list[Corretor]:
    """List all active (non-removed) corretores for the tenant."""
    result = await db.execute(
        select(Corretor).where(
            Corretor.tenant_id == tenant_id,
            Corretor.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, corretor: Corretor) -> Corretor:
    """Persist a new corretor."""
    db.add(corretor)
    await db.commit()
    await db.refresh(corretor)
    return corretor


async def save(db: AsyncSession, corretor: Corretor) -> Corretor:
    """Persist changes made to an existing corretor."""
    await db.commit()
    await db.refresh(corretor)
    return corretor
