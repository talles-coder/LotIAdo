"""Corretores module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.corretores.application.corretor_service import CorretorService
from app.corretores.domain.exceptions import CorretorNaoEncontradoError
from app.corretores.interface.schemas import (
    CorretorCreateRequest,
    CorretorResponse,
    CorretorUpdateRequest,
)
from app.identity.interface.dependencies import get_current_tenant_id
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(prefix="/corretores", tags=["corretores"])


@router.post("", response_model=CorretorResponse, status_code=status.HTTP_201_CREATED)
async def criar_corretor(
    request: CorretorCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> CorretorResponse:
    """Cadastra um novo corretor para o tenant autenticado."""
    service = CorretorService(db)
    corretor = await service.criar(tenant_id, request.nome, request.contato, request.usuario_id)
    return CorretorResponse.model_validate(corretor)


@router.get("", response_model=list[CorretorResponse])
async def listar_corretores(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[CorretorResponse]:
    """Lista os corretores ativos do tenant autenticado."""
    service = CorretorService(db)
    corretores = await service.listar(tenant_id)
    return [CorretorResponse.model_validate(corretor) for corretor in corretores]


@router.get("/{corretor_id}", response_model=CorretorResponse)
async def obter_corretor(
    corretor_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> CorretorResponse:
    """Retorna um corretor ativo do tenant autenticado."""
    service = CorretorService(db)
    try:
        corretor = await service.obter(tenant_id, corretor_id)
    except CorretorNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corretor não encontrado")
    return CorretorResponse.model_validate(corretor)


@router.patch("/{corretor_id}", response_model=CorretorResponse)
async def atualizar_corretor(
    corretor_id: UUID,
    request: CorretorUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> CorretorResponse:
    """Atualiza os campos informados de um corretor ativo do tenant autenticado."""
    service = CorretorService(db)
    try:
        corretor = await service.atualizar(
            tenant_id,
            corretor_id,
            nome=request.nome,
            contato=request.contato,
            usuario_id=request.usuario_id,
        )
    except CorretorNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corretor não encontrado")
    return CorretorResponse.model_validate(corretor)


@router.delete("/{corretor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_corretor(
    corretor_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> None:
    """Remove logicamente (soft-delete) um corretor do tenant autenticado."""
    service = CorretorService(db)
    try:
        await service.remover(tenant_id, corretor_id)
    except CorretorNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corretor não encontrado")
