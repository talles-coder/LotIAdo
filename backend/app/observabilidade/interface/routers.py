"""Observabilidade module HTTP routes."""
from fastapi import APIRouter, Depends

from app.identity.interface.dependencies import require_permission
from app.observabilidade.application.metricas_service import MetricasIAService
from app.observabilidade.interface.schemas import MetricasIAResponse

router = APIRouter(prefix="/observabilidade", tags=["observabilidade"])


@router.get("/metricas", response_model=MetricasIAResponse, dependencies=[Depends(require_permission("observabilidade:visualizar"))])
async def obter_metricas() -> MetricasIAResponse:
    """Métricas agregadas de chamadas de IA (latência, volume, taxa de erro), por origem e no total.

    Lê o log estruturado gerado por `OllamaLLMProvider` (FASE10-IMPL-01) — não é
    escopado por tenant: reflete o uso de IA da instância do backend inteira
    (só admin/gestor enxergam, via `observabilidade:visualizar`), não os dados
    de negócio de um tenant específico. Aceitável no volume de portfólio; se
    isso vier a importar (múltiplos tenants reais), o evento logado precisaria
    carregar `tenant_id`.
    """
    metricas = MetricasIAService().obter_metricas()
    return MetricasIAResponse(
        total_chamadas=metricas.total_chamadas,
        chamadas_com_erro=metricas.chamadas_com_erro,
        taxa_erro=metricas.taxa_erro,
        latencia_media_ms=metricas.latencia_media_ms,
        por_origem=[
            {
                "origem": item.origem,
                "total_chamadas": item.total_chamadas,
                "chamadas_com_erro": item.chamadas_com_erro,
                "latencia_media_ms": item.latencia_media_ms,
            }
            for item in metricas.por_origem
        ],
    )
