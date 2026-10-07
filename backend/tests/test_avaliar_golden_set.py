"""Testes do runner de avaliação do golden-set (SCRUM-114): parte pura, sem Ollama/Postgres.

`scripts.avaliar_golden_set.avaliar_golden_set()` em si (que chama os services
reais) não é testado aqui — precisa de Ollama + Postgres reais, não cabe numa
suíte de CI rápida. Ver handoff de SCRUM-114 em
docs/backlog/fase-10-observabilidade-evaluation.md para os resultados de
corridas reais (incluindo a demonstração de detecção de regressão via
faithfulness).
"""
from unittest.mock import AsyncMock

import pytest

from eval.faithfulness import calcular_faithfulness
from eval.ids import LOTE_IDS, LOTEAMENTO_ID, id_deterministico
from scripts.avaliar_golden_set import _passou_contem_todos, _resolver_placeholders


def test_passou_contem_todos_lista_vazia_sempre_passa():
    assert _passou_contem_todos("qualquer coisa", []) is True


def test_passou_contem_todos_exige_todas_as_substrings_case_insensitive():
    assert _passou_contem_todos("O lote GE-01 está Disponível", ["ge-01", "disponível"]) is True
    assert _passou_contem_todos("O lote GE-01 está reservado", ["ge-01", "disponível"]) is False


def test_passou_contem_todos_substrings_separadas_toleram_frase_diferente():
    """`["não", "encontr"]` (2 entradas) bate tanto com 'não encontrei' quanto 'não consegui encontrar'."""
    assert _passou_contem_todos("Não encontrei nada.", ["não", "encontr"]) is True
    assert _passou_contem_todos("Não consegui encontrar o lote.", ["não", "encontr"]) is True


def test_resolver_placeholders_substitui_ids_deterministicos():
    pergunta = _resolver_placeholders("Distância entre {lote_ge_01} e {lote_ge_04} no loteamento {loteamento_id}?")
    assert str(LOTE_IDS["GE-01"]) in pergunta
    assert str(LOTE_IDS["GE-04"]) in pergunta
    assert str(LOTEAMENTO_ID) in pergunta


def test_resolver_placeholders_lote_inexistente_nao_colide_com_ids_reais():
    pergunta = _resolver_placeholders("Área do lote {lote_inexistente}?")
    assert str(id_deterministico("lote-inexistente")) in pergunta
    assert str(LOTE_IDS["GE-01"]) not in pergunta


@pytest.mark.asyncio
async def test_calcular_faithfulness_parseia_json_do_juiz():
    llm = AsyncMock()
    llm.generate.return_value = '{"faithfulness": 0.8, "justificativa": "quase tudo sustentado"}'

    score, justificativa = await calcular_faithfulness(llm, contexto="prazo de entrega: 12 meses", resposta="12 meses")

    assert score == 0.8
    assert justificativa == "quase tudo sustentado"


@pytest.mark.asyncio
async def test_calcular_faithfulness_sem_contexto_nao_chama_o_juiz():
    llm = AsyncMock()

    score, justificativa = await calcular_faithfulness(llm, contexto="", resposta="qualquer resposta")

    assert score == 0.0
    llm.generate.assert_not_called()


@pytest.mark.asyncio
async def test_calcular_faithfulness_juiz_retorna_texto_invalido_nao_lanca_excecao():
    llm = AsyncMock()
    llm.generate.return_value = "desculpe, não consigo avaliar isso."

    score, justificativa = await calcular_faithfulness(llm, contexto="algo", resposta="algo")

    assert score == 0.0
    assert "não retornou JSON válido" in justificativa
