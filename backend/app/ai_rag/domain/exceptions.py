"""AI RAG domain exceptions."""


class LoteamentoDaBuscaNaoEncontradoError(Exception):
    """Raised when `loteamento_id` informado na busca não existe (ou não é do tenant)."""


class LoteDaBuscaNaoEncontradoError(Exception):
    """Raised when `lote_id` informado na busca não existe (ou não é do tenant)."""
