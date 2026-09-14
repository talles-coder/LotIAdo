"""Cliente use cases."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.clientes.domain.models import Cliente
from app.clientes.infrastructure.repository import (
    create,
    get_by_id,
    list_by_tenant,
    save,
)


class ClienteService:
    """Orchestrates CRUD operations for clientes, scoped to a tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar(self, tenant_id: UUID, nome: str, documento: str, contato: str) -> Cliente:
        """Create a new cliente for the tenant."""
        cliente = Cliente(tenant_id=tenant_id, nome=nome, documento=documento, contato=contato)
        return await create(self.db, cliente)

    async def listar(self, tenant_id: UUID) -> list[Cliente]:
        """List all active clientes for the tenant."""
        return await list_by_tenant(self.db, tenant_id)

    async def obter(self, tenant_id: UUID, cliente_id: UUID) -> Cliente:
        """Fetch a single active cliente, raising if not found in the tenant."""
        cliente = await get_by_id(self.db, tenant_id, cliente_id)
        if cliente is None:
            raise ClienteNaoEncontradoError()
        return cliente

    async def atualizar(
        self,
        tenant_id: UUID,
        cliente_id: UUID,
        nome: str | None = None,
        documento: str | None = None,
        contato: str | None = None,
    ) -> Cliente:
        """Update the given fields of an active cliente."""
        cliente = await self.obter(tenant_id, cliente_id)
        if nome is not None:
            cliente.nome = nome
        if documento is not None:
            cliente.documento = documento
        if contato is not None:
            cliente.contato = contato
        return await save(self.db, cliente)

    async def remover(self, tenant_id: UUID, cliente_id: UUID) -> None:
        """Soft-delete a cliente (não hard-delete)."""
        cliente = await self.obter(tenant_id, cliente_id)
        cliente.deleted_at = datetime.now(timezone.utc)
        await save(self.db, cliente)
