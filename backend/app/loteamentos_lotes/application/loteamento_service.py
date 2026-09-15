"""Loteamento use cases."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.loteamentos_lotes.domain.exceptions import LoteamentoNaoEncontradoError
from app.loteamentos_lotes.domain.models import Loteamento
from app.loteamentos_lotes.infrastructure.repository import (
    create_loteamento,
    get_loteamento_by_id,
    list_loteamentos_by_tenant,
    save_loteamento,
)


class LoteamentoService:
    """Orchestrates CRUD operations for loteamentos, scoped to a tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar(self, tenant_id: UUID, nome: str, descricao: str | None = None) -> Loteamento:
        """Create a new loteamento for the tenant."""
        loteamento = Loteamento(tenant_id=tenant_id, nome=nome, descricao=descricao)
        return await create_loteamento(self.db, loteamento)

    async def listar(self, tenant_id: UUID) -> list[Loteamento]:
        """List all active loteamentos for the tenant."""
        return await list_loteamentos_by_tenant(self.db, tenant_id)

    async def obter(self, tenant_id: UUID, loteamento_id: UUID) -> Loteamento:
        """Fetch a single active loteamento, raising if not found in the tenant."""
        loteamento = await get_loteamento_by_id(self.db, tenant_id, loteamento_id)
        if loteamento is None:
            raise LoteamentoNaoEncontradoError()
        return loteamento

    async def atualizar(
        self,
        tenant_id: UUID,
        loteamento_id: UUID,
        nome: str | None = None,
        descricao: str | None = None,
    ) -> Loteamento:
        """Update the given fields of an active loteamento."""
        loteamento = await self.obter(tenant_id, loteamento_id)
        if nome is not None:
            loteamento.nome = nome
        if descricao is not None:
            loteamento.descricao = descricao
        return await save_loteamento(self.db, loteamento)

    async def remover(self, tenant_id: UUID, loteamento_id: UUID) -> None:
        """Soft-delete a loteamento (não hard-delete)."""
        loteamento = await self.obter(tenant_id, loteamento_id)
        loteamento.deleted_at = datetime.now(timezone.utc)
        await save_loteamento(self.db, loteamento)
