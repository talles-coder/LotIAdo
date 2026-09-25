"""Testes de integração do módulo geo: geometria de lotes e feições de referência."""
import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, Polygon
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.domain.models import FeicaoReferencia, TipoFeicao
from app.geo.infrastructure.repository import create_feicao, list_feicoes_by_loteamento
from app.loteamentos_lotes.domain.models import Lote, Loteamento
from app.tenancy.domain.models import Tenant


async def _criar_loteamento(db: AsyncSession) -> tuple[Tenant, Loteamento]:
    tenant = Tenant(name="geo", slug="geo")
    db.add(tenant)
    await db.flush()
    loteamento = Loteamento(tenant_id=tenant.id, nome="Residencial Geo")
    db.add(loteamento)
    await db.commit()
    return tenant, loteamento


@pytest.mark.asyncio
async def test_lote_e_rua_adjacente_se_tocam(db_session: AsyncSession):
    tenant, loteamento = await _criar_loteamento(db_session)

    # Lote quadrado de 0.001° de lado; a rua corre ao longo da sua aresta inferior.
    lote = Lote(
        tenant_id=tenant.id,
        loteamento_id=loteamento.id,
        identificacao="L1",
        geometria=from_shape(Polygon([(0, 0), (0.001, 0), (0.001, 0.001), (0, 0.001)]), srid=4326),
    )
    db_session.add(lote)
    await db_session.commit()
    rua = await create_feicao(
        db_session,
        FeicaoReferencia(
            tenant_id=tenant.id,
            loteamento_id=loteamento.id,
            tipo=TipoFeicao.RUA,
            nome="Rua A",
            geometria=from_shape(LineString([(-0.001, 0), (0.002, 0)]), srid=4326),
        ),
    )

    toca = await db_session.scalar(
        select(func.ST_Touches(Lote.geometria, FeicaoReferencia.geometria))
        .select_from(Lote)
        .join(FeicaoReferencia, FeicaoReferencia.loteamento_id == Lote.loteamento_id)
        .where(Lote.id == lote.id, FeicaoReferencia.id == rua.id)
    )
    assert toca is True


@pytest.mark.asyncio
async def test_lista_feicoes_do_loteamento(db_session: AsyncSession):
    tenant, loteamento = await _criar_loteamento(db_session)
    await create_feicao(
        db_session,
        FeicaoReferencia(
            tenant_id=tenant.id,
            loteamento_id=loteamento.id,
            tipo=TipoFeicao.AREA_VERDE,
            geometria=from_shape(Polygon([(0, 0), (1, 0), (1, 1)]), srid=4326),
        ),
    )

    feicoes = await list_feicoes_by_loteamento(db_session, tenant.id, loteamento.id)

    assert [f.tipo for f in feicoes] == [TipoFeicao.AREA_VERDE]
