"""Clientes module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clientes.application.cliente_service import ClienteService
from app.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.clientes.interface.schemas import (
    ClienteCreateRequest,
    ClienteResponse,
    ClienteUpdateRequest,
)
from app.identity.interface.dependencies import get_current_tenant_id
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def criar_cliente(
    request: ClienteCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> ClienteResponse:
    """Cadastra um novo cliente para o tenant autenticado."""
    service = ClienteService(db)
    cliente = await service.criar(tenant_id, request.nome, request.documento, request.contato)
    return ClienteResponse.model_validate(cliente)


@router.get("", response_model=list[ClienteResponse])
async def listar_clientes(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[ClienteResponse]:
    """Lista os clientes ativos do tenant autenticado."""
    service = ClienteService(db)
    clientes = await service.listar(tenant_id)
    return [ClienteResponse.model_validate(cliente) for cliente in clientes]


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(
    cliente_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> ClienteResponse:
    """Retorna um cliente ativo do tenant autenticado."""
    service = ClienteService(db)
    try:
        cliente = await service.obter(tenant_id, cliente_id)
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return ClienteResponse.model_validate(cliente)


@router.patch("/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(
    cliente_id: UUID,
    request: ClienteUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> ClienteResponse:
    """Atualiza os campos informados de um cliente ativo do tenant autenticado."""
    service = ClienteService(db)
    try:
        cliente = await service.atualizar(
            tenant_id,
            cliente_id,
            nome=request.nome,
            documento=request.documento,
            contato=request.contato,
        )
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return ClienteResponse.model_validate(cliente)


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_cliente(
    cliente_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> None:
    """Remove logicamente (soft-delete) um cliente do tenant autenticado."""
    service = ClienteService(db)
    try:
        await service.remover(tenant_id, cliente_id)
    except ClienteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
