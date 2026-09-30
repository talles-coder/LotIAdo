"""Schemas HTTP das consultas espaciais."""
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.loteamentos_lotes.domain.state_machine import LoteStatus


class DistanciaResponse(BaseModel):
    distancia_m: float


class LotesDentroDeRequest(BaseModel):
    area_geojson: dict = Field(description="GeoJSON Polygon/MultiPolygon, SRID 4326, [lng, lat]")
    loteamento_id: UUID | None = None
    status: LoteStatus | None = None
    area_m2_min: Decimal | None = Field(default=None, ge=0)
