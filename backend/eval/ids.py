"""IDs determinísticos do tenant de avaliação (golden-set, FASE10-IMPL-03/SCRUM-113).

`scripts/seed_golden_set.py` (cria os dados) e `scripts/avaliar_golden_set.py`
(lê `eval/golden_set.yaml` e roda contra eles) importam só isso — nenhum UUID
literal aparece no YAML nem em nenhum dos dois scripts. Mudar um nome aqui
muda o dado que `golden_set.yaml` referencia por esse nome; não renomeie sem
atualizar o YAML junto.
"""
from uuid import NAMESPACE_URL, UUID, uuid5

TENANT_SLUG = "golden-set"
TENANT_NOME = "Golden Eval"
USUARIO_EMAIL = "golden@test.com"
USUARIO_SENHA = "senha123"


def id_deterministico(nome: str) -> UUID:
    """UUID v5 estável para `nome` — mesmo `nome` sempre gera o mesmo id, sem precisar guardá-lo em lugar nenhum."""
    return uuid5(NAMESPACE_URL, f"lotiado-golden-set:{nome}")


TENANT_ID = id_deterministico("tenant")
USUARIO_ID = id_deterministico("usuario")
LOTEAMENTO_ID = id_deterministico("loteamento")

RUA_A_ID = id_deterministico("rua-a")
RUA_B_ID = id_deterministico("rua-b")
AREA_VERDE_ID = id_deterministico("area-verde")

LOTE_IDS = {
    "GE-01": id_deterministico("lote-ge-01"),
    "GE-02": id_deterministico("lote-ge-02"),
    "GE-03": id_deterministico("lote-ge-03"),
    "GE-04": id_deterministico("lote-ge-04"),
}

DOCUMENTO_ID = id_deterministico("documento-memorial")
