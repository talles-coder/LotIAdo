"""Testes do logging estruturado de chamadas ao LLMProvider (SCRUM-109)."""
import logging

import pytest

from app.observabilidade.domain.chamada_ia import OrigemChamadaIA
from app.observabilidade.infrastructure.context import (
    contexto_origem_ia,
    contexto_request_id,
    origem_ia_atual,
    request_id_atual,
)
from app.observabilidade.infrastructure.llm_logging import medir_chamada_llm
from app.observabilidade.infrastructure.logging_config import JsonFormatter


def test_contexto_origem_ia_e_request_id_isolados_por_escopo():
    assert origem_ia_atual() is None
    assert request_id_atual() is None

    with contexto_request_id("req-1"), contexto_origem_ia(OrigemChamadaIA.RAG):
        assert request_id_atual() == "req-1"
        assert origem_ia_atual() is OrigemChamadaIA.RAG

    assert origem_ia_atual() is None
    assert request_id_atual() is None


def test_medir_chamada_llm_loga_sucesso_com_tokens_e_contexto(caplog):
    caplog.set_level(logging.INFO, logger="app.ia")

    with contexto_request_id("req-2"), contexto_origem_ia(OrigemChamadaIA.AGENTE):
        with medir_chamada_llm(metodo="chat", modelo="llama3") as resultado:
            resultado["tokens_entrada"] = 10
            resultado["tokens_saida"] = 3

    (record,) = caplog.records
    payload = dict(record.msg)
    latencia_ms = payload.pop("latencia_ms")
    assert latencia_ms >= 0
    assert payload == {
        "request_id": "req-2",
        "origem": "agente",
        "metodo": "chat",
        "modelo": "llama3",
        "tokens_entrada": 10,
        "tokens_saida": 3,
        "sucesso": True,
    }


def test_medir_chamada_llm_loga_erro_e_relanca_excecao(caplog):
    caplog.set_level(logging.INFO, logger="app.ia")

    with pytest.raises(RuntimeError, match="ollama indisponível"):
        with medir_chamada_llm(metodo="generate", modelo="llama3"):
            raise RuntimeError("ollama indisponível")

    (record,) = caplog.records
    assert record.msg["sucesso"] is False
    assert record.msg["erro"] == "ollama indisponível"
    assert record.msg["origem"] == OrigemChamadaIA.DESCONHECIDA.value


def test_medir_chamada_llm_sem_contexto_gera_request_id_de_fallback(caplog):
    caplog.set_level(logging.INFO, logger="app.ia")

    with medir_chamada_llm(metodo="embed", modelo="nomic-embed-text"):
        pass

    (record,) = caplog.records
    assert record.msg["request_id"]  # uuid gerado, não vazio
    assert record.msg["origem"] == OrigemChamadaIA.DESCONHECIDA.value


def test_json_formatter_serializa_dict_estruturado():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.ia", level=logging.INFO, pathname=__file__, lineno=1, msg={"sucesso": True}, args=None, exc_info=None
    )
    saida = formatter.format(record)
    assert '"sucesso": true' in saida
    assert '"level": "INFO"' in saida
    assert '"logger": "app.ia"' in saida


def test_json_formatter_serializa_mensagem_texto_comum():
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="outro.logger", level=logging.WARNING, pathname=__file__, lineno=1, msg="algo aconteceu", args=None, exc_info=None
    )
    saida = formatter.format(record)
    assert '"message": "algo aconteceu"' in saida
