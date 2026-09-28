"""Métricas estilo Ragas (faithfulness) via LLM-as-juiz, sem a lib `ragas` (FASE10-IMPL-04/SCRUM-114).

`pip install ragas` força upgrade de `langgraph` (0.2.60 -> 1.2.x) e de
`langchain-text-splitters` — breaking change que quebraria `app.ai_agents`
(depende da API 0.2.x de `StateGraph`/`MemorySaver`) e `app.ai_rag.infrastructure
.chunking`. Confirmado com `pip install --dry-run ragas` antes de decidir isso
(ver handoff de SCRUM-114 em docs/backlog/), não é suposição.

Ragas continua sendo a referência conceitual (decisão D7,
docs/03-decisoes-tecnicas.md): este módulo implementa a métrica mais usada de
lá — faithfulness via LLM-as-juiz, sem treino nem dependência extra — só sem a
lib pesada. Reavaliar se/quando o backend isolar o avaliador num venv próprio
(ela não precisa compartilhar processo com a API).
"""
import json
import re

from app.ai_rag.infrastructure.llm_provider import LLMProvider

_PROMPT_FAITHFULNESS = """Você avalia se uma RESPOSTA é sustentada pelo CONTEXTO abaixo, sem inventar nada que não esteja lá.

CONTEXTO:
{contexto}

RESPOSTA:
{resposta}

Responda apenas um JSON no formato {{"faithfulness": <0.0 a 1.0>, "justificativa": "<uma frase>"}}, onde 1.0 significa que toda afirmação da resposta é sustentada pelo contexto, e 0.0 que a resposta contradiz ou inventa informação não presente no contexto. Se a resposta disser explicitamente que não encontrou informação, e isso for verdade (o contexto não contém a resposta), dê 1.0 (é o comportamento correto, não uma invenção)."""


async def calcular_faithfulness(llm: LLMProvider, *, contexto: str, resposta: str) -> tuple[float, str]:
    """Pede pro LLM (mesmo `ollama_generation_model` do app) julgar se `resposta` é sustentada por `contexto`.

    Retorna `(score, justificativa)`. Se o juiz não devolver um JSON válido, retorna
    `(0.0, "...")` — falha visível (score mínimo), nunca lançamos exceção que interromperia a avaliação inteira.
    """
    if not contexto.strip():
        return 0.0, "sem contexto recuperado para julgar"

    saida = await llm.generate(_PROMPT_FAITHFULNESS.format(contexto=contexto, resposta=resposta))
    match = re.search(r"\{.*\}", saida, re.DOTALL)
    if match is None:
        return 0.0, f"juiz não retornou JSON válido: {saida[:200]!r}"
    try:
        dados = json.loads(match.group(0))
        return float(dados["faithfulness"]), str(dados.get("justificativa", ""))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return 0.0, f"juiz não retornou JSON válido: {saida[:200]!r}"
