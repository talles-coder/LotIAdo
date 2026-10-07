"""AI agents module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.application.agente_service import AgenteService, ResultadoAgente
from app.ai_agents.domain.exceptions import ConfirmacaoNaoEncontradaError
from app.ai_agents.interface.schemas import (
    ConfirmacaoAcaoPendente,
    ConfirmarAcaoRequest,
    PerguntarAgenteRequest,
    PerguntarAgenteResponse,
)
from app.identity.interface.dependencies import get_current_tenant_id
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(tags=["ai_agents"])


def _resposta_http(resultado: ResultadoAgente) -> PerguntarAgenteResponse:
    confirmacao = (
        ConfirmacaoAcaoPendente(
            confirmacao_id=resultado.confirmacao.confirmacao_id,
            tool=resultado.confirmacao.tool,
            descricao=resultado.confirmacao.descricao,
            argumentos=resultado.confirmacao.argumentos,
        )
        if resultado.confirmacao is not None
        else None
    )
    return PerguntarAgenteResponse(resposta=resultado.resposta, confirmacao=confirmacao)


@router.post("/agente/perguntar", response_model=PerguntarAgenteResponse, response_model_exclude_none=True)
async def perguntar(
    payload: PerguntarAgenteRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> PerguntarAgenteResponse:
    """Pergunta em linguagem natural respondida pelo agente, que decide e executa tools sobre os dados do tenant.

    Se o agente propuser uma ação sensível (cancelar reserva, alterar preço,
    alterar responsável), a resposta vem com `confirmacao` preenchida em vez
    de `resposta` — o cliente deve chamar `POST /agente/confirmar` com o
    `confirmacao_id` recebido para aprovar ou recusar antes de qualquer
    execução real.
    """
    service = AgenteService(db)
    resultado = await service.perguntar(tenant_id, payload.pergunta)
    return _resposta_http(resultado)


@router.post("/agente/confirmar", response_model=PerguntarAgenteResponse, response_model_exclude_none=True)
async def confirmar(
    payload: ConfirmarAcaoRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> PerguntarAgenteResponse:
    """Aprova ou recusa uma ação sensível proposta por `POST /agente/perguntar`."""
    service = AgenteService(db)
    try:
        resultado = await service.confirmar(tenant_id, payload.confirmacao_id, payload.aprovado)
    except ConfirmacaoNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Confirmação pendente não encontrada")
    return _resposta_http(resultado)
