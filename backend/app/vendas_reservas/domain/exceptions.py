"""Vendas_reservas domain exceptions."""
from uuid import UUID


class ReservaNaoEncontradaError(Exception):
    """Raised when a reserva id does not match a reserva in the tenant."""


class LoteNaoDisponivelParaReservaError(Exception):
    """Raised when a lote is not in a state that allows creating a reserva for it."""

    def __init__(self, lote_id: UUID):
        self.lote_id = lote_id
        super().__init__(f"Lote '{lote_id}' não está disponível para reserva")


class ReservaNaoEstaAtivaError(Exception):
    """Raised when trying to convert-to-venda or cancel a reserva that is not RESERVADO."""
