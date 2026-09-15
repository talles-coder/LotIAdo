"""Lote use cases, incluindo validação de transição de status pela máquina de estados."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.loteamentos_lotes.domain.exceptions import (
    LoteNaoEncontradoError,
    TransicaoDeStatusInvalidaError,
)
from app.loteamentos_lotes.domain.models import Lote
from app.loteamentos_lotes.domain.state_machine import LoteStatus, transicao_e_permitida
from app.loteamentos_lotes.infrastructure.repository import (
    create_lote,
    get_lote_by_id,
    list_lotes_by_loteamento,
    save_lote,
)


class LoteService:
    """Orchestrates CRUD and status transitions for lotes, scoped to a tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar(
        self,
        tenant_id: UUID,
        loteamento_id: UUID,
        identificacao: str,
        quadra: str | None = None,
        area_m2: Decimal | None = None,
        preco: Decimal | None = None,
        caracteristicas: dict | None = None,
    ) -> Lote:
        """Create a new lote under the given loteamento, starting as DISPONIVEL."""
        lote = Lote(
            tenant_id=tenant_id,
            loteamento_id=loteamento_id,
            identificacao=identificacao,
            quadra=quadra,
            area_m2=area_m2,
            preco=preco,
            caracteristicas=caracteristicas or {},
        )
        return await create_lote(self.db, lote)

    async def listar(self, tenant_id: UUID, loteamento_id: UUID) -> list[Lote]:
        """List all active lotes for a loteamento."""
        return await list_lotes_by_loteamento(self.db, tenant_id, loteamento_id)

    async def obter(self, tenant_id: UUID, lote_id: UUID) -> Lote:
        """Fetch a single active lote, raising if not found in the tenant."""
        lote = await get_lote_by_id(self.db, tenant_id, lote_id)
        if lote is None:
            raise LoteNaoEncontradoError()
        return lote

    async def atualizar(
        self,
        tenant_id: UUID,
        lote_id: UUID,
        quadra: str | None = None,
        area_m2: Decimal | None = None,
        preco: Decimal | None = None,
        caracteristicas: dict | None = None,
        corretor_id: UUID | None = None,
        cliente_id: UUID | None = None,
    ) -> Lote:
        """Update the given fields of an active lote (status is not editable here)."""
        lote = await self.obter(tenant_id, lote_id)
        if quadra is not None:
            lote.quadra = quadra
        if area_m2 is not None:
            lote.area_m2 = area_m2
        if preco is not None:
            lote.preco = preco
        if caracteristicas is not None:
            lote.caracteristicas = caracteristicas
        if corretor_id is not None:
            lote.corretor_id = corretor_id
        if cliente_id is not None:
            lote.cliente_id = cliente_id
        return await save_lote(self.db, lote)

    async def transicionar_status(
        self, tenant_id: UUID, lote_id: UUID, novo_status: LoteStatus
    ) -> Lote:
        """Apply a status transition, validating it against the state machine first."""
        lote = await self.obter(tenant_id, lote_id)
        if not transicao_e_permitida(lote.status, novo_status):
            raise TransicaoDeStatusInvalidaError(lote.status, novo_status)
        lote.status = novo_status
        return await save_lote(self.db, lote)

    async def remover(self, tenant_id: UUID, lote_id: UUID) -> None:
        """Soft-delete a lote (não hard-delete)."""
        lote = await self.obter(tenant_id, lote_id)
        lote.deleted_at = datetime.now(timezone.utc)
        await save_lote(self.db, lote)
