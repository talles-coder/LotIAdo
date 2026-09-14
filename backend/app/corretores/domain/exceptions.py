"""Corretores domain exceptions."""


class CorretorNaoEncontradoError(Exception):
    """Raised when a corretor id does not match an active corretor in the tenant."""
