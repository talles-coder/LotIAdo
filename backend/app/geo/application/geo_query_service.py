"""Consultas espaciais determinísticas, reutilizáveis (API REST hoje, agente de IA na Fase 9)."""
from decimal import Decimal
from uuid import UUID

from geoalchemy2.shape import from_shape
from shapely.errors import ShapelyError
from shapely.geometry import shape
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.domain.exceptions import (
    AreaInvalidaError,
    FeicaoNaoEncontradaError,
    LoteSemGeometriaError,
)
from app.geo.infrastructure.repository import (
    get_distancia_m,
    get_feicao_by_id,
    list_lotes_de_esquina,
    list_lotes_dentro_de,
    list_lotes_proximos_de,
)
from app.loteamentos_lotes.domain.exceptions import LoteNaoEncontradoError
from app.loteamentos_lotes.domain.models import Lote
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.loteamentos_lotes.infrastructure.repository import get_lote_by_id


class GeoQueryService:
    """Consultas espaciais combinadas com filtros de negócio (status, área mínima), por tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def distancia_entre_lotes(self, tenant_id: UUID, lote_a_id: UUID, lote_b_id: UUID) -> float:
        """Distância mínima em metros entre os perímetros de dois lotes (0 se vizinhos)."""
        await self._obter_lote_com_geometria(tenant_id, lote_a_id)
        await self._obter_lote_com_geometria(tenant_id, lote_b_id)
        return await get_distancia_m(self.db, lote_a_id, lote_b_id)

    async def lotes_de_esquina(
        self,
        tenant_id: UUID,
        loteamento_id: UUID,
        status: LoteStatus | None = None,
        area_m2_min: Decimal | None = None,
    ) -> list[Lote]:
        """Lotes que tocam ao menos duas ruas distintas do loteamento."""
        return await list_lotes_de_esquina(self.db, tenant_id, loteamento_id, status, area_m2_min)

    async def lotes_proximos_de(
        self,
        tenant_id: UUID,
        feicao_id: UUID,
        raio_m: float,
        status: LoteStatus | None = None,
        area_m2_min: Decimal | None = None,
    ) -> list[Lote]:
        """Lotes do loteamento da feição a até `raio_m` metros dela."""
        feicao = await get_feicao_by_id(self.db, tenant_id, feicao_id)
        if feicao is None:
            raise FeicaoNaoEncontradaError()
        return await list_lotes_proximos_de(self.db, tenant_id, feicao, raio_m, status, area_m2_min)

    async def lotes_dentro_de(
        self,
        tenant_id: UUID,
        area_geojson: dict,
        loteamento_id: UUID | None = None,
        status: LoteStatus | None = None,
        area_m2_min: Decimal | None = None,
    ) -> list[Lote]:
        """Lotes totalmente contidos em uma área GeoJSON (Polygon/MultiPolygon, [lng, lat])."""
        try:
            area = shape(area_geojson)
        except (ShapelyError, ValueError, KeyError, TypeError, AttributeError) as exc:
            raise AreaInvalidaError("GeoJSON inválido") from exc
        if area.geom_type not in ("Polygon", "MultiPolygon") or not area.is_valid:
            raise AreaInvalidaError("A área deve ser um Polygon ou MultiPolygon válido")
        return await list_lotes_dentro_de(
            self.db, tenant_id, from_shape(area, srid=4326), loteamento_id, status, area_m2_min
        )

    async def _obter_lote_com_geometria(self, tenant_id: UUID, lote_id: UUID) -> Lote:
        lote = await get_lote_by_id(self.db, tenant_id, lote_id)
        if lote is None:
            raise LoteNaoEncontradoError()
        if lote.geometria is None:
            raise LoteSemGeometriaError()
        return lote
