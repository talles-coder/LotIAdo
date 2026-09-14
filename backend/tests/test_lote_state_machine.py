"""Testes unitários (domínio puro, sem banco) da máquina de estados do lote."""
import pytest

from app.loteamentos_lotes.domain.state_machine import LoteStatus, transicao_e_permitida


@pytest.mark.parametrize(
    "atual,novo,esperado",
    [
        # DISPONIVEL
        (LoteStatus.DISPONIVEL, LoteStatus.RESERVADO, True),
        (LoteStatus.DISPONIVEL, LoteStatus.INDISPONIVEL, True),
        (LoteStatus.DISPONIVEL, LoteStatus.VENDIDO, False),
        (LoteStatus.DISPONIVEL, LoteStatus.DISPONIVEL, False),
        # RESERVADO
        (LoteStatus.RESERVADO, LoteStatus.VENDIDO, True),
        (LoteStatus.RESERVADO, LoteStatus.DISPONIVEL, True),
        (LoteStatus.RESERVADO, LoteStatus.INDISPONIVEL, False),
        (LoteStatus.RESERVADO, LoteStatus.RESERVADO, False),
        # VENDIDO (terminal — nenhuma transição de saída)
        (LoteStatus.VENDIDO, LoteStatus.DISPONIVEL, False),
        (LoteStatus.VENDIDO, LoteStatus.RESERVADO, False),
        (LoteStatus.VENDIDO, LoteStatus.INDISPONIVEL, False),
        (LoteStatus.VENDIDO, LoteStatus.VENDIDO, False),
        # INDISPONIVEL (só retorna a DISPONIVEL)
        (LoteStatus.INDISPONIVEL, LoteStatus.DISPONIVEL, True),
        (LoteStatus.INDISPONIVEL, LoteStatus.RESERVADO, False),
        (LoteStatus.INDISPONIVEL, LoteStatus.VENDIDO, False),
        (LoteStatus.INDISPONIVEL, LoteStatus.INDISPONIVEL, False),
    ],
)
def test_transicao_e_permitida(atual: LoteStatus, novo: LoteStatus, esperado: bool):
    """Cobre cada uma das 16 combinações (4x4) de origem/destino da tabela de transições."""
    assert transicao_e_permitida(atual, novo) is esperado
