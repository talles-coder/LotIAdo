"""Clientes domain exceptions."""


class ClienteNaoEncontradoError(Exception):
    """Raised when a cliente id does not match an active cliente in the tenant."""
