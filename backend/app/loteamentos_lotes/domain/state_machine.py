"""Máquina de estados finita para o status do lote (domínio Python puro, sem I/O)."""
from enum import Enum


class LoteStatus(str, Enum):
    """Estados possíveis de um lote."""

    DISPONIVEL = "disponivel"
    RESERVADO = "reservado"
    VENDIDO = "vendido"
    INDISPONIVEL = "indisponivel"


TRANSICOES_PERMITIDAS: dict[LoteStatus, frozenset[LoteStatus]] = {
    LoteStatus.DISPONIVEL: frozenset({LoteStatus.RESERVADO, LoteStatus.INDISPONIVEL}),
    LoteStatus.RESERVADO: frozenset({LoteStatus.VENDIDO, LoteStatus.DISPONIVEL}),
    LoteStatus.VENDIDO: frozenset(),
    LoteStatus.INDISPONIVEL: frozenset({LoteStatus.DISPONIVEL}),
}
"""Tabela de transições: de qual status é possível ir para quais outros.

VENDIDO é terminal (nenhuma transição de saída). INDISPONIVEL só retorna a
DISPONIVEL (ex.: pendência documental resolvida) — não pode ir direto para
RESERVADO/VENDIDO.
"""


def transicao_e_permitida(atual: LoteStatus, novo: LoteStatus) -> bool:
    """Verifica se a transição de `atual` para `novo` é permitida pela máquina de estados."""
    return novo in TRANSICOES_PERMITIDAS[atual]
