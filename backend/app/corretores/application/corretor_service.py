"""Corretor use cases."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.corretores.domain.exceptions import CorretorNaoEncontradoError
from app.corretores.domain.models import Corretor
from app.corretores.infrastructure.repository import (
    create,
    get_by_id,
    list_by_tenant,
    save,
)


class CorretorService:
    """Orchestrates CRUD operations for corretores, scoped to a tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar(
        self, tenant_id: UUID, nome: str, contato: str, usuario_id: UUID | None = None
    ) -> Corretor:
        """Create a new corretor for the tenant."""
        corretor = Corretor(tenant_id=tenant_id, nome=nome, contato=contato, usuario_id=usuario_id)
        return await create(self.db, corretor)

    async def listar(self, tenant_id: UUID) -> list[Corretor]:
        """List all active corretores for the tenant."""
        return await list_by_tenant(self.db, tenant_id)

    async def obter(self, tenant_id: UUID, corretor_id: UUID) -> Corretor:
        """Fetch a single active corretor, raising if not found in the tenant."""
        corretor = await get_by_id(self.db, tenant_id, corretor_id)
        if corretor is None:
            raise CorretorNaoEncontradoError()
        return corretor

    async def atualizar(
        self,
        tenant_id: UUID,
        corretor_id: UUID,
        nome: str | None = None,
        contato: str | None = None,
        usuario_id: UUID | None = None,
    ) -> Corretor:
        """Update the given fields of an active corretor."""
        corretor = await self.obter(tenant_id, corretor_id)
        if nome is not None:
            corretor.nome = nome
        if contato is not None:
            corretor.contato = contato
        if usuario_id is not None:
            corretor.usuario_id = usuario_id
        return await save(self.db, corretor)

    async def remover(self, tenant_id: UUID, corretor_id: UUID) -> None:
        """Soft-delete a corretor (não hard-delete)."""
        corretor = await self.obter(tenant_id, corretor_id)
        corretor.deleted_at = datetime.now(timezone.utc)
        await save(self.db, corretor)
