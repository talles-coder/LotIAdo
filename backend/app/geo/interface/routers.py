"""Geo module HTTP routes: consultas espaciais determinísticas."""
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.application.geo_query_service import GeoQueryService
from app.geo.domain.exceptions import (
    AreaInvalidaError,
    FeicaoNaoEncontradaError,
    LoteSemGeometriaError,
)
from app.geo.interface.schemas import DistanciaResponse, LotesDentroDeRequest
from app.identity.interface.dependencies import get_current_tenant_id
from app.loteamentos_lotes.domain.exceptions import LoteNaoEncontradoError
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.loteamentos_lotes.interface.schemas import LoteResponse
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/distancia", response_model=DistanciaResponse)
async def distancia_entre_lotes(
    lote_a: UUID,
    lote_b: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> DistanciaResponse:
    """Distância mínima em metros entre dois lotes do tenant."""
    try:
        distancia = await GeoQueryService(db).distancia_entre_lotes(tenant_id, lote_a, lote_b)
    except LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")
    except LoteSemGeometriaError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Lote sem geometria cadastrada"
        )
    return DistanciaResponse(distancia_m=distancia)


@router.get("/loteamentos/{loteamento_id}/lotes-de-esquina", response_model=list[LoteResponse])
async def lotes_de_esquina(
    loteamento_id: UUID,
    status_lote: LoteStatus | None = Query(default=None, alias="status"),
    area_m2_min: Decimal | None = Query(default=None, ge=0),
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[LoteResponse]:
    """Lotes de esquina (tocam ao menos duas ruas) do loteamento, com filtros opcionais."""
    lotes = await GeoQueryService(db).lotes_de_esquina(
        tenant_id, loteamento_id, status_lote, area_m2_min
    )
    return [LoteResponse.model_validate(lote) for lote in lotes]


@router.get("/feicoes/{feicao_id}/lotes-proximos", response_model=list[LoteResponse])
async def lotes_proximos_de_feicao(
    feicao_id: UUID,
    raio_m: float = Query(gt=0),
    status_lote: LoteStatus | None = Query(default=None, alias="status"),
    area_m2_min: Decimal | None = Query(default=None, ge=0),
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[LoteResponse]:
    """Lotes a até `raio_m` metros de uma feição de referência (ex.: área verde)."""
    try:
        lotes = await GeoQueryService(db).lotes_proximos_de(
            tenant_id, feicao_id, raio_m, status_lote, area_m2_min
        )
    except FeicaoNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feição não encontrada")
    return [LoteResponse.model_validate(lote) for lote in lotes]


@router.post("/lotes/dentro-de", response_model=list[LoteResponse])
async def lotes_dentro_de_area(
    request: LotesDentroDeRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[LoteResponse]:
    """Lotes totalmente contidos em uma área GeoJSON (POST porque a área vai no corpo)."""
    try:
        lotes = await GeoQueryService(db).lotes_dentro_de(
            tenant_id,
            request.area_geojson,
            loteamento_id=request.loteamento_id,
            status=request.status,
            area_m2_min=request.area_m2_min,
        )
    except AreaInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return [LoteResponse.model_validate(lote) for lote in lotes]
