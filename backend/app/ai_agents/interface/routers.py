"""AI agents module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.application.agente_service import AgenteService
from app.ai_agents.interface.schemas import PerguntarAgenteRequest, PerguntarAgenteResponse
from app.identity.interface.dependencies import get_current_tenant_id
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(tags=["ai_agents"])


@router.post("/agente/perguntar", response_model=PerguntarAgenteResponse)
async def perguntar(
    payload: PerguntarAgenteRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> PerguntarAgenteResponse:
    """Pergunta em linguagem natural respondida pelo agente, que decide e executa tools sobre os dados do tenant."""
    service = AgenteService(db)
    resposta = await service.perguntar(tenant_id, payload.pergunta)
    return PerguntarAgenteResponse(resposta=resposta)
