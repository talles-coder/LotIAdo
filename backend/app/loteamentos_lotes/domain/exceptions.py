"""Loteamentos_lotes domain exceptions."""
from app.loteamentos_lotes.domain.state_machine import LoteStatus


class LoteamentoNaoEncontradoError(Exception):
    """Raised when a loteamento id does not match an active loteamento in the tenant."""


class LoteNaoEncontradoError(Exception):
    """Raised when a lote id does not match an active lote in the tenant."""


class MapeamentoDeImportacaoInvalidoError(Exception):
    """Raised when the column mapping for a CSV import is missing required fields
    or references columns that don't exist in the file."""


class TransicaoDeStatusInvalidaError(Exception):
    """Raised when a lote status transition is not allowed by the state machine."""

    def __init__(self, atual: LoteStatus, novo: LoteStatus):
        self.atual = atual
        self.novo = novo
        super().__init__(f"Transição de '{atual.value}' para '{novo.value}' não é permitida")
