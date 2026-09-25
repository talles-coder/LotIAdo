"""Database access for the geo module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.domain.models import FeicaoReferencia


async def create_feicao(db: AsyncSession, feicao: FeicaoReferencia) -> FeicaoReferencia:
    """Persist a new reference feature. Sem `refresh()` — ver nota em loteamentos_lotes."""
    db.add(feicao)
    await db.commit()
    return feicao


async def list_feicoes_by_loteamento(
    db: AsyncSession, tenant_id: UUID, loteamento_id: UUID
) -> list[FeicaoReferencia]:
    """List active reference features of a loteamento, scoped to the tenant."""
    result = await db.execute(
        select(FeicaoReferencia).where(
            FeicaoReferencia.tenant_id == tenant_id,
            FeicaoReferencia.loteamento_id == loteamento_id,
            FeicaoReferencia.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())
