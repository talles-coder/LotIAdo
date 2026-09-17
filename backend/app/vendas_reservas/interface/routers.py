"""Vendas_reservas module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.corretores.domain.exceptions import CorretorNaoEncontradoError
from app.identity.interface.dependencies import get_current_tenant_id
from app.loteamentos_lotes.domain.exceptions import LoteNaoEncontradoError
from app.tenancy.interface.dependencies import get_tenant_scoped_db
from app.vendas_reservas.application.reserva_service import ReservaService
from app.vendas_reservas.domain.exceptions import (
    LoteNaoDisponivelParaReservaError,
    ReservaNaoEncontradaError,
    ReservaNaoEstaAtivaError,
)
from app.vendas_reservas.interface.schemas import ReservaCreateRequest, ReservaResponse

router = APIRouter(prefix="/reservas", tags=["vendas_reservas"])


@router.post("", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
async def criar_reserva(
    request: ReservaCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> ReservaResponse:
    """Reserva um lote disponível para um cliente do tenant autenticado."""
    service = ReservaService(db)
    try:
        reserva = await service.criar_reserva(
            tenant_id, request.lote_id, request.cliente_id, request.corretor_id
        )
    except LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    except CorretorNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corretor não encontrado")
    except LoteNaoDisponivelParaReservaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return ReservaResponse.model_validate(reserva)


@router.post("/{reserva_id}/converter-venda", response_model=ReservaResponse)
async def converter_venda(
    reserva_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> ReservaResponse:
    """Converte uma reserva ativa em venda, movendo o lote para VENDIDO."""
    service = ReservaService(db)
    try:
        reserva = await service.converter_para_venda(tenant_id, reserva_id)
    except ReservaNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")
    except ReservaNaoEstaAtivaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reserva não está ativa (já foi convertida em venda ou cancelada)",
        )
    except LoteNaoDisponivelParaReservaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return ReservaResponse.model_validate(reserva)


@router.post("/{reserva_id}/cancelar", response_model=ReservaResponse)
async def cancelar_reserva(
    reserva_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> ReservaResponse:
    """Cancela uma reserva ativa, devolvendo o lote para DISPONIVEL."""
    service = ReservaService(db)
    try:
        reserva = await service.cancelar(tenant_id, reserva_id)
    except ReservaNaoEncontradaError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva não encontrada")
    except ReservaNaoEstaAtivaError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reserva não está ativa (já foi convertida em venda ou cancelada)",
        )
    except LoteNaoDisponivelParaReservaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return ReservaResponse.model_validate(reserva)
