"""Ai_agents domain exceptions."""


class ConfirmacaoNaoEncontradaError(Exception):
    """Raised when a `confirmacao_id` não corresponde a uma pausa de confirmação pendente do tenant."""
