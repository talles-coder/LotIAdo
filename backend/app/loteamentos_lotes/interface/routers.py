"""Loteamentos_lotes module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.identity.interface.dependencies import get_current_tenant_id, require_permission
from app.loteamentos_lotes.application.lote_service import LoteService
from app.loteamentos_lotes.application.loteamento_service import LoteamentoService
from app.loteamentos_lotes.domain.exceptions import (
    LoteamentoNaoEncontradoError,
    LoteNaoEncontradoError,
    TransicaoDeStatusInvalidaError,
)
from app.loteamentos_lotes.interface.schemas import (
    LoteamentoCreateRequest,
    LoteamentoResponse,
    LoteamentoUpdateRequest,
    LoteCreateRequest,
    LoteResponse,
    LoteStatusUpdateRequest,
    LoteUpdateRequest,
)
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(tags=["loteamentos_lotes"])


@router.post("/loteamentos", response_model=LoteamentoResponse, status_code=status.HTTP_201_CREATED)
async def criar_loteamento(
    request: LoteamentoCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    _: None = Depends(require_permission("loteamentos_lotes:gerenciar")),
) -> LoteamentoResponse:
    """Cadastra um novo loteamento para o tenant autenticado."""
    service = LoteamentoService(db)
    loteamento = await service.criar(tenant_id, request.nome, request.descricao)
    return LoteamentoResponse.model_validate(loteamento)


@router.get("/loteamentos", response_model=list[LoteamentoResponse])
async def listar_loteamentos(
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[LoteamentoResponse]:
    """Lista os loteamentos ativos do tenant autenticado."""
    service = LoteamentoService(db)
    loteamentos = await service.listar(tenant_id)
    return [LoteamentoResponse.model_validate(loteamento) for loteamento in loteamentos]


@router.get("/loteamentos/{loteamento_id}", response_model=LoteamentoResponse)
async def obter_loteamento(
    loteamento_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> LoteamentoResponse:
    """Retorna um loteamento ativo do tenant autenticado."""
    service = LoteamentoService(db)
    try:
        loteamento = await service.obter(tenant_id, loteamento_id)
    except LoteamentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loteamento não encontrado")
    return LoteamentoResponse.model_validate(loteamento)


@router.patch("/loteamentos/{loteamento_id}", response_model=LoteamentoResponse)
async def atualizar_loteamento(
    loteamento_id: UUID,
    request: LoteamentoUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    _: None = Depends(require_permission("loteamentos_lotes:gerenciar")),
) -> LoteamentoResponse:
    """Atualiza os campos informados de um loteamento ativo do tenant autenticado."""
    service = LoteamentoService(db)
    try:
        loteamento = await service.atualizar(
            tenant_id, loteamento_id, nome=request.nome, descricao=request.descricao
        )
    except LoteamentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loteamento não encontrado")
    return LoteamentoResponse.model_validate(loteamento)


@router.delete("/loteamentos/{loteamento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_loteamento(
    loteamento_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    _: None = Depends(require_permission("loteamentos_lotes:gerenciar")),
) -> None:
    """Remove logicamente (soft-delete) um loteamento do tenant autenticado."""
    service = LoteamentoService(db)
    try:
        await service.remover(tenant_id, loteamento_id)
    except LoteamentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loteamento não encontrado")


@router.post(
    "/loteamentos/{loteamento_id}/lotes",
    response_model=LoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def criar_lote(
    loteamento_id: UUID,
    request: LoteCreateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    _: None = Depends(require_permission("loteamentos_lotes:gerenciar")),
) -> LoteResponse:
    """Cadastra um novo lote (status inicial DISPONIVEL) em um loteamento do tenant autenticado."""
    loteamento_service = LoteamentoService(db)
    try:
        await loteamento_service.obter(tenant_id, loteamento_id)
    except LoteamentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loteamento não encontrado")

    lote_service = LoteService(db)
    lote = await lote_service.criar(
        tenant_id,
        loteamento_id,
        request.identificacao,
        quadra=request.quadra,
        area_m2=request.area_m2,
        preco=request.preco,
        caracteristicas=request.caracteristicas,
    )
    return LoteResponse.model_validate(lote)


@router.get("/loteamentos/{loteamento_id}/lotes", response_model=list[LoteResponse])
async def listar_lotes(
    loteamento_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> list[LoteResponse]:
    """Lista os lotes ativos de um loteamento do tenant autenticado."""
    service = LoteService(db)
    lotes = await service.listar(tenant_id, loteamento_id)
    return [LoteResponse.model_validate(lote) for lote in lotes]


@router.get("/lotes/{lote_id}", response_model=LoteResponse)
async def obter_lote(
    lote_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
) -> LoteResponse:
    """Retorna um lote ativo do tenant autenticado."""
    service = LoteService(db)
    try:
        lote = await service.obter(tenant_id, lote_id)
    except LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")
    return LoteResponse.model_validate(lote)


@router.patch("/lotes/{lote_id}", response_model=LoteResponse)
async def atualizar_lote(
    lote_id: UUID,
    request: LoteUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    _: None = Depends(require_permission("loteamentos_lotes:gerenciar")),
) -> LoteResponse:
    """Atualiza os campos informados de um lote ativo (status não é editável aqui)."""
    service = LoteService(db)
    try:
        lote = await service.atualizar(
            tenant_id,
            lote_id,
            quadra=request.quadra,
            area_m2=request.area_m2,
            preco=request.preco,
            caracteristicas=request.caracteristicas,
            corretor_id=request.corretor_id,
            cliente_id=request.cliente_id,
        )
    except LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")
    return LoteResponse.model_validate(lote)


@router.patch("/lotes/{lote_id}/status", response_model=LoteResponse)
async def transicionar_status_lote(
    lote_id: UUID,
    request: LoteStatusUpdateRequest,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    _: None = Depends(require_permission("loteamentos_lotes:gerenciar")),
) -> LoteResponse:
    """Transiciona o status de um lote, validando contra a máquina de estados."""
    service = LoteService(db)
    try:
        lote = await service.transicionar_status(tenant_id, lote_id, request.status)
    except LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")
    except TransicaoDeStatusInvalidaError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return LoteResponse.model_validate(lote)


@router.delete("/lotes/{lote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_lote(
    lote_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    _: None = Depends(require_permission("loteamentos_lotes:gerenciar")),
) -> None:
    """Remove logicamente (soft-delete) um lote do tenant autenticado."""
    service = LoteService(db)
    try:
        await service.remover(tenant_id, lote_id)
    except LoteNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")
