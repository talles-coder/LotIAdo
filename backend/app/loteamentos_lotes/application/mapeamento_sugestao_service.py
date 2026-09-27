"""Sugestão de mapeamento coluna->campo do CSV via LLM (FASE8-IMPL-01/SCRUM-97).

Só sugere; a confirmação humana continua obrigatória no fluxo de
`LoteImportService.importar` (ver `lote_import_service.py`) — este serviço nunca
persiste nada, apenas pré-preenche a tela de mapeamento (Fase 5) com um "palpite"
editável do LLM, cada um com um nível de confiança.
"""
import json
import logging

from pydantic import BaseModel, ValidationError

import app.ai_rag as ai_rag
from app.loteamentos_lotes.application.lote_import_service import CAMPOS_MAPEAVEIS

logger = logging.getLogger(__name__)

MAX_TENTATIVAS = 2


class _SugestaoCampo(BaseModel):
    campo: str
    coluna: str | None = None
    confianca: float = 0.0


class _SugestaoDeMapeamento(BaseModel):
    sugestoes: list[_SugestaoCampo]


class MapeamentoSugestaoService:
    """Pede ao `LLMProvider` uma sugestão de mapeamento coluna->campo para cabeçalhos de um CSV."""

    async def sugerir(self, colunas: list[str]) -> dict[str, tuple[str, float]]:
        """Retorna `{campo: (coluna, confianca)}` só para campos com coluna sugerida.

        Se o LLM não devolver um JSON válido após as tentativas, retorna vazio — a tela de
        mapeamento cai de volta ao fluxo 100% manual, sem quebrar a importação.
        """
        prompt = _montar_prompt(colunas)
        colunas_validas = set(colunas)
        erro_anterior: str | None = None

        for _ in range(MAX_TENTATIVAS):
            texto = await ai_rag.llm_provider.generate(_prompt_com_erro(prompt, erro_anterior))
            try:
                dados = json.loads(_extrair_json(texto))
                sugestao = _SugestaoDeMapeamento.model_validate(dados)
            except (json.JSONDecodeError, ValidationError) as exc:
                erro_anterior = str(exc)
                logger.warning("Sugestão de mapeamento de CSV inválida, tentando novamente: %s", erro_anterior)
                continue
            return _filtrar(sugestao, colunas_validas)

        return {}


def _filtrar(sugestao: _SugestaoDeMapeamento, colunas_validas: set[str]) -> dict[str, tuple[str, float]]:
    resultado: dict[str, tuple[str, float]] = {}
    for item in sugestao.sugestoes:
        if item.campo not in CAMPOS_MAPEAVEIS:
            continue
        if item.coluna is None or item.coluna not in colunas_validas:
            continue
        resultado[item.campo] = (item.coluna, item.confianca)
    return resultado


def _montar_prompt(colunas: list[str]) -> str:
    campos = ", ".join(CAMPOS_MAPEAVEIS)
    return (
        "Você mapeia colunas de um CSV de lotes imobiliários para campos fixos de um sistema.\n"
        f"Campos possíveis: {campos}.\n"
        "Responda APENAS com um JSON (sem texto antes ou depois), no formato:\n"
        '{"sugestoes": [{"campo": "identificacao", "coluna": "<cabeçalho exato do CSV ou null>", '
        '"confianca": <0.0 a 1.0>}, ...]}\n'
        "Inclua uma entrada para cada campo possível. Se nenhum cabeçalho corresponder a um campo, "
        "use coluna null e confianca 0.\n\n"
        f"Cabeçalhos do CSV: {json.dumps(colunas, ensure_ascii=False)}"
    )


def _prompt_com_erro(prompt: str, erro_anterior: str | None) -> str:
    if erro_anterior is None:
        return prompt
    return f"{prompt}\n\nSua resposta anterior não era um JSON válido ({erro_anterior}). Responda de novo, só com o JSON."


def _extrair_json(texto: str) -> str:
    """Modelos locais às vezes envolvem o JSON em texto/markdown; extrai só o objeto `{...}`."""
    inicio = texto.find("{")
    fim = texto.rfind("}")
    if inicio == -1 or fim == -1 or fim < inicio:
        return texto
    return texto[inicio : fim + 1]
