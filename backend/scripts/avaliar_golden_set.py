"""Roda o golden-set (FASE10-IMPL-03) contra o RAG e o agente reais e gera um relatório (FASE10-IMPL-04/SCRUM-114).

Uso:
    cd backend
    python -m scripts.seed_golden_set        # uma vez (idempotente)
    python -m scripts.avaliar_golden_set

Requer Ollama local rodando. Cada execução grava um relatório JSON em
`eval/reports/<timestamp>.json` (git-ignorado) e imprime um resumo no
terminal. Rodar duas vezes seguidas deve produzir taxas de aprovação estáveis
(`contem_todos`) — a métrica de `faithfulness` (LLM-as-juiz) tem alguma
variância esperada do próprio LLM, mas não deveria oscilar entre "sustentado"
e "inventado" para o mesmo par pergunta/contexto.
"""
import asyncio
import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_agents.application.agente_service import AgenteService
from app.ai_rag.application.pergunta_service import PerguntaService
from app.database import async_session
from eval.config import GOLDEN_SET_PATH, REPORTS_DIR
from eval.faithfulness import calcular_faithfulness
from eval.ids import LOTE_IDS, LOTEAMENTO_ID, TENANT_ID, TENANT_SLUG, id_deterministico

# UUID determinístico (mesmo mecanismo de eval/ids.py), sintaticamente válido mas
# garantidamente ausente do tenant de teste — fixo entre execuções, senão o caso
# "não inventa" não seria reprodutível (violaria o critério de aceite de
# SCRUM-114: "rodar duas vezes... métricas estáveis").
_LOTE_INEXISTENTE = id_deterministico("lote-inexistente")


def _resolver_placeholders(pergunta: str) -> str:
    return pergunta.format(
        loteamento_id=LOTEAMENTO_ID,
        lote_ge_01=LOTE_IDS["GE-01"],
        lote_ge_04=LOTE_IDS["GE-04"],
        lote_inexistente=_LOTE_INEXISTENTE,
    )


@dataclass
class ResultadoCaso:
    id: str
    tipo: str
    pergunta: str
    resposta: str
    criterio_aceitacao: str
    contem_todos_esperado: list[str]
    passou_contem_todos: bool
    faithfulness: float | None = None
    faithfulness_justificativa: str | None = None
    erro: str | None = None


@dataclass
class Relatorio:
    gerado_em: str
    tenant_slug: str
    modelo: str
    total_casos: int
    casos_passaram: int
    faithfulness_medio: float | None
    casos: list[ResultadoCaso] = field(default_factory=list)


async def _set_tenant(db: AsyncSession) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(TENANT_ID)})


def _passou_contem_todos(resposta: str, esperado: list[str]) -> bool:
    if not esperado:
        return True  # caso sem checagem automática — avaliado só por faithfulness ou revisão manual do criterio_aceitacao
    resposta_lower = resposta.lower()
    return all(substr.lower() in resposta_lower for substr in esperado)


async def _avaliar_caso_rag(db: AsyncSession, caso: dict) -> ResultadoCaso:
    service = PerguntaService(db)
    resultado = await service.perguntar(TENANT_ID, caso["pergunta"])
    contexto = "\n\n".join(fonte.trecho for fonte in resultado.fontes)

    faithfulness, justificativa = await calcular_faithfulness(ai_rag.llm_provider, contexto=contexto, resposta=resultado.resposta)

    return ResultadoCaso(
        id=caso["id"], tipo="rag", pergunta=caso["pergunta"], resposta=resultado.resposta,
        criterio_aceitacao=caso["criterio_aceitacao"], contem_todos_esperado=caso.get("contem_todos", []),
        passou_contem_todos=_passou_contem_todos(resultado.resposta, caso.get("contem_todos", [])),
        faithfulness=faithfulness, faithfulness_justificativa=justificativa,
    )


async def _avaliar_caso_agente(db: AsyncSession, caso: dict) -> ResultadoCaso:
    service = AgenteService(db)
    resultado = await service.perguntar(TENANT_ID, caso["pergunta"])
    resposta = resultado.resposta if resultado.resposta is not None else f"[pausou aguardando confirmação: {resultado.confirmacao}]"

    return ResultadoCaso(
        id=caso["id"], tipo="agente", pergunta=caso["pergunta"], resposta=resposta,
        criterio_aceitacao=caso["criterio_aceitacao"], contem_todos_esperado=caso.get("contem_todos", []),
        passou_contem_todos=_passou_contem_todos(resposta, caso.get("contem_todos", [])),
    )


async def avaliar_golden_set() -> Relatorio:
    golden_set = yaml.safe_load(GOLDEN_SET_PATH.read_text(encoding="utf-8"))
    casos_config = golden_set["casos"]
    for caso in casos_config:
        caso["pergunta"] = _resolver_placeholders(caso["pergunta"])

    resultados: list[ResultadoCaso] = []
    for caso in casos_config:
        async with async_session() as db:
            await _set_tenant(db)
            try:
                if caso["tipo"] == "rag":
                    resultado = await _avaliar_caso_rag(db, caso)
                elif caso["tipo"] == "agente":
                    resultado = await _avaliar_caso_agente(db, caso)
                else:
                    raise ValueError(f"tipo de caso desconhecido: {caso['tipo']!r}")
            except Exception as exc:  # noqa: BLE001 — um caso quebrando não deve derrubar a avaliação inteira
                resultado = ResultadoCaso(
                    id=caso["id"], tipo=caso["tipo"], pergunta=caso["pergunta"], resposta="",
                    criterio_aceitacao=caso["criterio_aceitacao"], contem_todos_esperado=caso.get("contem_todos", []),
                    passou_contem_todos=False, erro=str(exc),
                )
            resultados.append(resultado)
            print(f"[{'OK' if resultado.passou_contem_todos and not resultado.erro else 'FALHOU'}] {resultado.id}")

    scores_faithfulness = [r.faithfulness for r in resultados if r.faithfulness is not None]
    return Relatorio(
        gerado_em=datetime.now(timezone.utc).isoformat(),
        tenant_slug=TENANT_SLUG,
        modelo=ai_rag.llm_provider.settings.ollama_generation_model,
        total_casos=len(resultados),
        casos_passaram=sum(1 for r in resultados if r.passou_contem_todos and not r.erro),
        faithfulness_medio=round(sum(scores_faithfulness) / len(scores_faithfulness), 3) if scores_faithfulness else None,
        casos=resultados,
    )


def _salvar_relatorio(relatorio: Relatorio) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    caminho = REPORTS_DIR / f"{relatorio.gerado_em.replace(':', '-')}.json"
    caminho.write_text(json.dumps(asdict(relatorio), ensure_ascii=False, indent=2), encoding="utf-8")
    return caminho


def _imprimir_resumo(relatorio: Relatorio) -> None:
    print("\n" + "=" * 70)
    print(f"Golden-set: {relatorio.casos_passaram}/{relatorio.total_casos} casos passaram (contém-todos)")
    if relatorio.faithfulness_medio is not None:
        print(f"Faithfulness médio (casos RAG): {relatorio.faithfulness_medio}")
    for caso in relatorio.casos:
        if caso.erro:
            print(f"  ERRO  {caso.id}: {caso.erro}")
        elif not caso.passou_contem_todos:
            print(f"  FALHOU {caso.id}: esperava {caso.contem_todos_esperado!r} em {caso.resposta[:120]!r}")
        elif caso.faithfulness is not None and caso.faithfulness < 0.5:
            print(f"  ATENÇÃO {caso.id}: faithfulness baixo ({caso.faithfulness}) — {caso.faithfulness_justificativa}")
    print("=" * 70)


def main() -> None:
    relatorio = asyncio.run(avaliar_golden_set())
    caminho = _salvar_relatorio(relatorio)
    _imprimir_resumo(relatorio)
    print(f"\nRelatório salvo em {caminho}")
    if relatorio.casos_passaram < relatorio.total_casos:
        sys.exit(1)  # útil pra rodar em CI/pre-merge e falhar o job em regressão


if __name__ == "__main__":
    main()
