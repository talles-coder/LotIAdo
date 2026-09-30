"""Database access for the geo module."""
from decimal import Decimal
from uuid import UUID

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.geo.domain.models import FeicaoReferencia, TipoFeicao
from app.loteamentos_lotes.domain.models import Lote
from app.loteamentos_lotes.domain.state_machine import LoteStatus


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


async def get_feicao_by_id(
    db: AsyncSession, tenant_id: UUID, feicao_id: UUID
) -> FeicaoReferencia | None:
    """Fetch an active reference feature by id, scoped to the tenant."""
    result = await db.execute(
        select(FeicaoReferencia).where(
            FeicaoReferencia.id == feicao_id,
            FeicaoReferencia.tenant_id == tenant_id,
            FeicaoReferencia.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


def _lotes_ativos(tenant_id: UUID, status: LoteStatus | None, area_m2_min: Decimal | None):
    """SELECT de lotes ativos do tenant com os filtros de negócio (status, área mínima)."""
    query = select(Lote).where(Lote.tenant_id == tenant_id, Lote.deleted_at.is_(None))
    if status is not None:
        query = query.where(Lote.status == status)
    if area_m2_min is not None:
        query = query.where(Lote.area_m2 >= area_m2_min)
    return query.order_by(Lote.identificacao)


async def get_distancia_m(db: AsyncSession, lote_a_id: UUID, lote_b_id: UUID) -> float:
    """Distância mínima em metros entre dois lotes (cálculo geodésico via geography)."""
    lote_b = aliased(Lote)
    return await db.scalar(
        select(func.ST_Distance(cast(Lote.geometria, Geography), cast(lote_b.geometria, Geography)))
        .where(Lote.id == lote_a_id, lote_b.id == lote_b_id)
    )


async def list_lotes_de_esquina(
    db: AsyncSession,
    tenant_id: UUID,
    loteamento_id: UUID,
    status: LoteStatus | None,
    area_m2_min: Decimal | None,
) -> list[Lote]:
    """Lotes que tocam pelo menos duas ruas distintas do mesmo loteamento."""
    ruas_tocadas = (
        select(func.count(FeicaoReferencia.id))
        .where(
            FeicaoReferencia.tenant_id == tenant_id,
            FeicaoReferencia.loteamento_id == Lote.loteamento_id,
            FeicaoReferencia.tipo == TipoFeicao.RUA,
            FeicaoReferencia.deleted_at.is_(None),
            func.ST_Touches(Lote.geometria, FeicaoReferencia.geometria),
        )
        .correlate(Lote)
        .scalar_subquery()
    )
    query = _lotes_ativos(tenant_id, status, area_m2_min).where(
        Lote.loteamento_id == loteamento_id, Lote.geometria.is_not(None), ruas_tocadas >= 2
    )
    return list((await db.execute(query)).scalars().all())


async def list_lotes_proximos_de(
    db: AsyncSession,
    tenant_id: UUID,
    feicao: FeicaoReferencia,
    raio_m: float,
    status: LoteStatus | None,
    area_m2_min: Decimal | None,
) -> list[Lote]:
    """Lotes do loteamento da feição a no máximo `raio_m` metros dela."""
    query = _lotes_ativos(tenant_id, status, area_m2_min).where(
        Lote.loteamento_id == feicao.loteamento_id,
        Lote.geometria.is_not(None),
        # Geometria da feição lida no próprio SQL: reenviar o WKB carregado como
        # parâmetro não converte para geography.
        func.ST_DWithin(
            cast(Lote.geometria, Geography),
            cast(
                select(FeicaoReferencia.geometria)
                .where(FeicaoReferencia.id == feicao.id)
                .scalar_subquery(),
                Geography,
            ),
            raio_m,
        ),
    )
    return list((await db.execute(query)).scalars().all())


async def list_lotes_dentro_de(
    db: AsyncSession,
    tenant_id: UUID,
    area_wkb,
    loteamento_id: UUID | None,
    status: LoteStatus | None,
    area_m2_min: Decimal | None,
) -> list[Lote]:
    """Lotes totalmente contidos na área informada (SRID 4326)."""
    query = _lotes_ativos(tenant_id, status, area_m2_min).where(
        Lote.geometria.is_not(None), func.ST_Within(Lote.geometria, area_wkb)
    )
    if loteamento_id is not None:
        query = query.where(Lote.loteamento_id == loteamento_id)
    return list((await db.execute(query)).scalars().all())
