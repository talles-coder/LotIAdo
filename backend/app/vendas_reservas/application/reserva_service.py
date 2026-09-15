"""Reserva/venda use cases.

Cada operação (criar reserva, converter em venda, cancelar) muda o `Lote`
e a `ReservaVenda` juntos, num único `commit` — se qualquer validação
falhar antes disso, nada é persistido (nem a reserva, nem a transição do
lote). A leitura do lote usa `SELECT ... FOR UPDATE`
(`get_lote_by_id_for_update`) para serializar tentativas concorrentes de
reservar o mesmo lote: a segunda tentativa só enxerga o lote depois que a
primeira transação commitar, e nesse ponto o status já não é mais
`DISPONIVEL`.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.loteamentos_lotes.domain.exceptions import LoteNaoEncontradoError
from app.loteamentos_lotes.domain.state_machine import LoteStatus, transicao_e_permitida
from app.loteamentos_lotes.infrastructure.repository import get_lote_by_id_for_update
from app.vendas_reservas.domain.exceptions import (
    LoteNaoDisponivelParaReservaError,
    ReservaNaoEncontradaError,
    ReservaNaoEstaAtivaError,
)
from app.vendas_reservas.domain.models import ReservaVenda, StatusReservaVenda, TipoReservaVenda
from app.vendas_reservas.infrastructure.repository import get_reserva_by_id


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
        await self.db.refresh(reserva)
        return reserva

    async def obter(self, tenant_id: UUID, reserva_id: UUID) -> ReservaVenda:
        """Fetch a single reserva/venda, raising if not found in the tenant."""
        reserva = await get_reserva_by_id(self.db, tenant_id, reserva_id)
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
        await self.db.refresh(reserva)
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
        await self.db.refresh(reserva)
        return reserva
