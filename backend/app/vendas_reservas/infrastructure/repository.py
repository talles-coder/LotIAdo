"""Database access for the vendas_reservas module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vendas_reservas.domain.models import ReservaVenda, StatusReservaVenda


async def get_reserva_by_id(db: AsyncSession, tenant_id: UUID, reserva_id: UUID) -> ReservaVenda | None:
    """Fetch a reserva/venda by id, scoped to the tenant."""
    result = await db.execute(
        select(ReservaVenda).where(
            ReservaVenda.id == reserva_id,
            ReservaVenda.tenant_id == tenant_id,
        )
    )
    return result.scalar_one_or_none()


async def get_reserva_atual_by_lote(
    db: AsyncSession, tenant_id: UUID, lote_id: UUID
) -> ReservaVenda | None:
    """Fetch the current (non-cancelada) reserva/venda for a lote, scoped to the tenant, if any.

    "Atual" cobre tanto uma reserva em aberto (`RESERVADO`) quanto uma venda já
    concretizada (`VENDIDO`) — a tela de detalhe do lote precisa do cliente em
    ambos os casos. Canceladas não contam; se o lote já teve uma reserva
    cancelada e uma nova em seguida, pega a mais recente por `created_at`.
    """
    result = await db.execute(
        select(ReservaVenda)
        .where(
            ReservaVenda.lote_id == lote_id,
            ReservaVenda.tenant_id == tenant_id,
            ReservaVenda.status != StatusReservaVenda.CANCELADA,
        )
        .order_by(ReservaVenda.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()
