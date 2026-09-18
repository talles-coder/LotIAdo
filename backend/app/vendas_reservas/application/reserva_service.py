"""Reserva/venda use cases.

Cada operação (criar reserva, converter em venda, cancelar) muda o `Lote`
e a `ReservaVenda` juntos, num único `commit` — se qualquer validação
falhar antes disso, nada é persistido (nem a reserva, nem a transição do
lote). A leitura do lote usa `SELECT ... FOR UPDATE`
(`get_lote_by_id_for_update`) para serializar tentativas concorrentes de
reservar o mesmo lote: a segunda tentativa só enxerga o lote depois que a
primeira transação commitar, e nesse ponto o status já não é mais
`DISPONIVEL`.

Sem `db.refresh()` depois do commit, de propósito (ver
app/tenancy/TENANT_CONVENTION.md e o mesmo comentário em
app/clientes/infrastructure/repository.py): a sessão tem
`expire_on_commit=False` e o objeto já está completo em memória; um
`refresh()` abriria uma *nova* transação sem `app.tenant_id` setado, e a
policy de RLS derrubaria a query.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.clientes.domain.exceptions import ClienteNaoEncontradoError
from app.clientes.infrastructure.repository import get_by_id as get_cliente_by_id
from app.corretores.domain.exceptions import CorretorNaoEncontradoError
from app.corretores.infrastructure.repository import get_by_id as get_corretor_by_id
from app.loteamentos_lotes.domain.exceptions import LoteNaoEncontradoError
from app.loteamentos_lotes.domain.state_machine import LoteStatus, transicao_e_permitida
from app.loteamentos_lotes.infrastructure.repository import get_lote_by_id_for_update
from app.vendas_reservas.domain.exceptions import (
    LoteNaoDisponivelParaReservaError,
    ReservaNaoEncontradaError,
    ReservaNaoEstaAtivaError,
)
from app.vendas_reservas.domain.models import ReservaVenda, StatusReservaVenda, TipoReservaVenda
from app.vendas_reservas.infrastructure.repository import get_reserva_ativa_by_lote, get_reserva_by_id


class ReservaService:
    """Orchestrates the reserva/venda lifecycle, scoped to a tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def criar_reserva(
        self,
        tenant_id: UUID,
        lote_id: UUID,
        cliente_id: UUID,
        corretor_id: UUID | None = None,
    ) -> ReservaVenda:
        """Reserva um lote disponível para um cliente, movendo o lote para RESERVADO.

        Atômico: a reserva só é criada se a transição do lote for válida, e
        ambas as mudanças são persistidas num único commit.
        """
        lote = await get_lote_by_id_for_update(self.db, tenant_id, lote_id)
        if lote is None:
            raise LoteNaoEncontradoError()
        if await get_cliente_by_id(self.db, tenant_id, cliente_id) is None:
            raise ClienteNaoEncontradoError()
        if corretor_id is not None and await get_corretor_by_id(self.db, tenant_id, corretor_id) is None:
            raise CorretorNaoEncontradoError()
        if not transicao_e_permitida(lote.status, LoteStatus.RESERVADO):
            raise LoteNaoDisponivelParaReservaError(lote_id)

        lote.status = LoteStatus.RESERVADO
        reserva = ReservaVenda(
            tenant_id=tenant_id,
            lote_id=lote_id,
            cliente_id=cliente_id,
            corretor_id=corretor_id,
            tipo=TipoReservaVenda.RESERVA,
            status=StatusReservaVenda.RESERVADO,
        )
        self.db.add(reserva)
        await self.db.commit()
        return reserva

    async def obter(self, tenant_id: UUID, reserva_id: UUID) -> ReservaVenda:
        """Fetch a single reserva/venda, raising if not found in the tenant."""
        reserva = await get_reserva_by_id(self.db, tenant_id, reserva_id)
        if reserva is None:
            raise ReservaNaoEncontradaError()
        return reserva

    async def obter_ativa_por_lote(self, tenant_id: UUID, lote_id: UUID) -> ReservaVenda:
        """Fetch the active (RESERVADO) reserva for a lote, raising if there is none."""
        reserva = await get_reserva_ativa_by_lote(self.db, tenant_id, lote_id)
        if reserva is None:
            raise ReservaNaoEncontradaError()
        return reserva

    async def converter_para_venda(self, tenant_id: UUID, reserva_id: UUID) -> ReservaVenda:
        """Converte uma reserva ativa em venda, movendo o lote para VENDIDO."""
        reserva = await self.obter(tenant_id, reserva_id)
        if reserva.status != StatusReservaVenda.RESERVADO:
            raise ReservaNaoEstaAtivaError()

        lote = await get_lote_by_id_for_update(self.db, tenant_id, reserva.lote_id)
        if lote is None or not transicao_e_permitida(lote.status, LoteStatus.VENDIDO):
            raise LoteNaoDisponivelParaReservaError(reserva.lote_id)

        lote.status = LoteStatus.VENDIDO
        reserva.status = StatusReservaVenda.VENDIDO
        reserva.tipo = TipoReservaVenda.VENDA
        await self.db.commit()
        return reserva

    async def cancelar(self, tenant_id: UUID, reserva_id: UUID) -> ReservaVenda:
        """Cancela uma reserva ativa, devolvendo o lote para DISPONIVEL."""
        reserva = await self.obter(tenant_id, reserva_id)
        if reserva.status != StatusReservaVenda.RESERVADO:
            raise ReservaNaoEstaAtivaError()

        lote = await get_lote_by_id_for_update(self.db, tenant_id, reserva.lote_id)
        if lote is None or not transicao_e_permitida(lote.status, LoteStatus.DISPONIVEL):
            raise LoteNaoDisponivelParaReservaError(reserva.lote_id)

        lote.status = LoteStatus.DISPONIVEL
        reserva.status = StatusReservaVenda.CANCELADA
        await self.db.commit()
        return reserva
