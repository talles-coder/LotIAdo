"""Identity domain exceptions."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials do not match a known, active user."""


class InvitationNaoEncontradoError(Exception):
    """Raised when an invitation token does not match a pending invitation."""


class InvitationExpiradoError(Exception):
    """Raised when an invitation token is past its expiration."""


class InvitationJaAceitoError(Exception):
    """Raised when an invitation token has already been used."""


class UsuarioJaAtivoNoTenantError(Exception):
    """Raised when inviting an email that already has an active membership in the tenant."""


class MembershipNaoEncontradaError(Exception):
    """Raised when a membership id does not match a membership in the tenant."""
