"""Documentos domain exceptions."""


class DocumentoNaoEncontradoError(Exception):
    """Raised when a documento id does not match an active documento in the tenant."""


class LoteamentoDoDocumentoNaoEncontradoError(Exception):
    """Raised when `loteamento_id` informado no upload não existe (ou não é do tenant)."""


class LoteDoDocumentoNaoEncontradoError(Exception):
    """Raised when `lote_id` informado no upload não existe (ou não é do tenant)."""
