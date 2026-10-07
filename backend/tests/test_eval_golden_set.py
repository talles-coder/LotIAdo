"""Testes do golden-set de avaliação (SCRUM-113): estrutura do YAML e IDs determinísticos.

Não toca Ollama/Postgres — `scripts.seed_golden_set` roda contra dados reais
(ver handoff em docs/backlog/fase-10-observabilidade-evaluation.md para os
resultados de uma corrida real); aqui só a estrutura estática.
"""
import yaml

from eval.config import GOLDEN_SET_PATH
from eval.ids import LOTE_IDS, TENANT_ID, id_deterministico


def test_ids_sao_deterministicos_entre_chamadas():
    assert id_deterministico("lote-ge-01") == id_deterministico("lote-ge-01")
    assert id_deterministico("lote-ge-01") != id_deterministico("lote-ge-02")


def test_lote_ids_nao_colidem_entre_si():
    assert len(set(LOTE_IDS.values())) == len(LOTE_IDS)
    assert TENANT_ID not in LOTE_IDS.values()


def test_golden_set_yaml_tem_pelo_menos_10_casos_com_campos_obrigatorios():
    """Critério de aceite de SCRUM-113: golden-set cobre >= 10 perguntas (RAG + agente)."""
    golden_set = yaml.safe_load(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    casos = golden_set["casos"]

    assert len(casos) >= 10
    tipos = {caso["tipo"] for caso in casos}
    assert tipos == {"rag", "agente"}
    ids = [caso["id"] for caso in casos]
    assert len(ids) == len(set(ids))  # sem id duplicado
    for caso in casos:
        assert caso["id"]
        assert caso["pergunta"]
        assert caso["criterio_aceitacao"]
        assert "contem_todos" in caso
