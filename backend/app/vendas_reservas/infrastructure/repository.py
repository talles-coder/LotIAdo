"""Database access for the vendas_reservas module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vendas_reservas.domain.models import ReservaVenda


async def get_reserva_by_id(db: AsyncSession, tenant_id: UUID, reserva_id: UUID) -> ReservaVenda | None:
    """Fetch a reserva/venda by id, scoped to the tenant."""
    result = await db.execute(
        select(ReservaVenda).where(
            ReservaVenda.id == reserva_id,
            ReservaVenda.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()
