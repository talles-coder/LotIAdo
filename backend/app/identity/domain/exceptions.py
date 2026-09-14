"""Identity domain exceptions."""


class InvalidCredentialsError(Exception):
    """Raised when login credentials do not match a known, active user."""
