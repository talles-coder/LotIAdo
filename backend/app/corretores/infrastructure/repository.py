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
    """Persist a new corretor.

    Sem `db.refresh()` de propósito: a sessão tem `expire_on_commit=False`
    (ver app/database.py) e o INSERT já traz os defaults gerados pelo server
    (`created_at`/`updated_at`) via `RETURNING`, então o objeto já está
    completo após o commit. Um `refresh()` abriria uma *nova* transação sem
    `app.tenant_id` setado — a policy de RLS derrubaria a query pra zero
    linhas (ver app/tenancy/interface/dependencies.py).
    """
    db.add(corretor)
    await db.commit()
    return corretor


async def save(db: AsyncSession, corretor: Corretor) -> Corretor:
    """Persist changes made to an existing corretor. Ver nota em `create()`."""
    await db.commit()
    return corretor
