"""Grafo do agente conversacional (FASE9-IMPL-02/03).

`StateGraph` (LangGraph) com quatro papéis: decisão (LLM com tool calling via
`LLMProvider.chat`), execução de tool de **consulta**, confirmação humana
antes de tool de **ação**, e formatação da resposta final. O laço
decidir -> executar_tool -> decidir se repete até o modelo responder sem
propor nova tool (ou até `MAX_CHAMADAS_TOOL`, para não travar em loop). O
agente nunca inventa dado: quando uma tool retorna "não encontrado", isso
vira uma mensagem de tool normal, e é o próprio modelo quem comunica a
ausência de resultado ao usuário (reforçado pelo `SYSTEM_PROMPT`).

Human-in-the-loop (FASE9-IMPL-03): quando o modelo propõe uma tool marcada
`acao=True` no `tool_registry` (cancelar reserva, alterar preço/responsável),
o grafo desvia para `confirmar_acao`, que pausa via `langgraph.types.interrupt`
em vez de executar a tool. `perguntar()` devolve uma `ConfirmacaoPendente`
nesse caso; o chamador (endpoint HTTP) decide e chama `confirmar()` com o
`confirmacao_id` retido — só então, se aprovado, a tool roda de fato, com a
auditoria automática (FASE1-IMPL-04) marcada com origem "agente"
(`app.audit.infrastructure.context.contexto_origem_auditoria`).

O checkpointer (`MemorySaver`) é um singleton do processo, não do tenant/
request: guarda o estado da pausa entre a chamada que interrompe e a que
resume (duas requests HTTP distintas). Isso é adequado para este projeto
(demonstrador local, um único processo) — não sobrevive a um restart nem
escala para múltiplas réplicas; se isso vier a importar, troque por um
checkpointer persistente (ex. Postgres) sem mudar a lógica do grafo.
"""
import json
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID, uuid4

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_agents.domain.exceptions import ConfirmacaoNaoEncontradaError
from app.ai_agents.infrastructure.tool_registry import TOOLS_POR_NOME, specs_para_llm
from app.audit.domain.acoes import OrigemAuditoria
from app.audit.infrastructure.context import contexto_origem_auditoria
from app.observabilidade.domain.chamada_ia import OrigemChamadaIA
from app.observabilidade.infrastructure.context import contexto_origem_ia

MAX_CHAMADAS_TOOL = 5

SYSTEM_PROMPT = (
    "Você é o assistente do LotIAdo, um sistema de gestão de loteamentos. "
    "Responda em português usando as tools disponíveis para consultar dados reais — "
    "nunca invente lotes, preços, clientes ou qualquer outro dado. "
    "Se uma tool indicar que não encontrou o que foi pedido, informe isso ao "
    "usuário em vez de supor um resultado. Tools de ação (cancelar reserva, "
    "alterar preço, alterar responsável) pausam automaticamente para "
    "confirmação humana — proponha-as normalmente quando o usuário pedir."
)

RESPOSTA_PADRAO_SEM_TEXTO = "Não consegui gerar uma resposta para essa pergunta."
MENSAGEM_ACAO_RECUSADA = "Ação recusada pelo usuário."

_CHECKPOINTER = MemorySaver()


class AgenteState(TypedDict):
    tenant_id: UUID
    mensagens: list[dict]
    chamadas_tool: int
    resposta: str


@dataclass(frozen=True)
class ConfirmacaoPendente:
    confirmacao_id: UUID
    tool: str
    descricao: str
    argumentos: dict


@dataclass(frozen=True)
class ResultadoAgente:
    resposta: str | None
    confirmacao: ConfirmacaoPendente | None


class AgenteService:
    """Orquestra o grafo do agente sobre uma sessão de banco já escopada ao tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._grafo = self._construir_grafo()

    async def perguntar(self, tenant_id: UUID, pergunta: str) -> ResultadoAgente:
        thread_id = uuid4()
        config = {"configurable": {"thread_id": str(thread_id)}}
        estado_inicial: AgenteState = {
            "tenant_id": tenant_id,
            "mensagens": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": pergunta},
            ],
            "chamadas_tool": 0,
            "resposta": "",
        }
        await self._grafo.ainvoke(estado_inicial, config=config)
        return await self._resultado_da_thread(thread_id, config)

    async def confirmar(self, tenant_id: UUID, confirmacao_id: UUID, aprovado: bool) -> ResultadoAgente:
        """Retoma um grafo pausado em `confirmar_acao`, aprovando ou recusando a ação proposta."""
        config = {"configurable": {"thread_id": str(confirmacao_id)}}
        estado = await self._grafo.aget_state(config)
        if not estado.next or estado.values.get("tenant_id") != tenant_id:
            raise ConfirmacaoNaoEncontradaError()
        # `Command(resume=False)` seria tratado como "sem write" pelo LangGraph
        # (checa `if cmd.resume:`, e `False` é falsy) — por isso o valor vai
        # embrulhado num dict, que é truthy independente de `aprovado`.
        await self._grafo.ainvoke(Command(resume={"aprovado": aprovado}), config=config)
        return await self._resultado_da_thread(confirmacao_id, config)

    async def _resultado_da_thread(self, thread_id: UUID, config: dict) -> ResultadoAgente:
        estado = await self._grafo.aget_state(config)
        if estado.next:
            payload = estado.tasks[0].interrupts[0].value
            return ResultadoAgente(
                resposta=None,
                confirmacao=ConfirmacaoPendente(confirmacao_id=thread_id, **payload),
            )
        return ResultadoAgente(resposta=estado.values["resposta"], confirmacao=None)

    def _construir_grafo(self):
        grafo = StateGraph(AgenteState)
        grafo.add_node("decidir", self._decidir)
        grafo.add_node("executar_tool", self._executar_tool)
        grafo.add_node("confirmar_acao", self._confirmar_acao)
        grafo.add_node("formatar_resposta", self._formatar_resposta)
        grafo.set_entry_point("decidir")
        grafo.add_conditional_edges(
            "decidir",
            self._rotear_apos_decisao,
            {"tool": "executar_tool", "acao": "confirmar_acao", "resposta": "formatar_resposta"},
        )
        grafo.add_edge("executar_tool", "decidir")
        grafo.add_edge("confirmar_acao", "decidir")
        grafo.add_edge("formatar_resposta", END)
        return grafo.compile(checkpointer=_CHECKPOINTER)

    async def _decidir(self, state: AgenteState) -> AgenteState:
        with contexto_origem_ia(OrigemChamadaIA.AGENTE):
            resposta = await ai_rag.llm_provider.chat(state["mensagens"], tools=specs_para_llm())
        mensagem_assistente: dict = {"role": "assistant", "content": resposta.conteudo or ""}
        if resposta.tool_calls:
            mensagem_assistente["tool_calls"] = [
                {"id": chamada.id, "function": {"name": chamada.nome, "arguments": chamada.argumentos}}
                for chamada in resposta.tool_calls
            ]
        return {**state, "mensagens": [*state["mensagens"], mensagem_assistente]}

    def _rotear_apos_decisao(self, state: AgenteState) -> str:
        ultima = state["mensagens"][-1]
        chamadas = ultima.get("tool_calls") or []
        if not chamadas or state["chamadas_tool"] >= MAX_CHAMADAS_TOOL:
            return "resposta"
        spec = TOOLS_POR_NOME.get(chamadas[0]["function"]["name"])
        return "acao" if spec is not None and spec.acao else "tool"

    async def _executar_tool(self, state: AgenteState) -> AgenteState:
        ultima = state["mensagens"][-1]
        mensagens_tool = [
            {
                "role": "tool",
                "tool_call_id": chamada["id"],
                "name": chamada["function"]["name"],
                "content": await self._chamar_tool(
                    state["tenant_id"], chamada["function"]["name"], chamada["function"]["arguments"]
                ),
            }
            for chamada in ultima.get("tool_calls", [])
        ]
        return {
            **state,
            "mensagens": [*state["mensagens"], *mensagens_tool],
            "chamadas_tool": state["chamadas_tool"] + 1,
        }

    async def _confirmar_acao(self, state: AgenteState) -> AgenteState:
        """Pausa antes de executar uma tool de ação, retomando só após aprovação humana explícita.

        Só a primeira `tool_call` do turno é tratada aqui — o `SYSTEM_PROMPT`
        e a rotina de decisão assumem uma tool proposta por vez, mesmo padrão
        já adotado em FASE9-IMPL-02 para tools de consulta.
        """
        ultima = state["mensagens"][-1]
        chamada = ultima["tool_calls"][0]
        nome, argumentos, tool_call_id = chamada["function"]["name"], chamada["function"]["arguments"], chamada["id"]
        spec = TOOLS_POR_NOME[nome]

        resumo = interrupt({"tool": nome, "descricao": spec.descricao, "argumentos": argumentos})
        aprovado = resumo["aprovado"]

        if aprovado:
            with contexto_origem_auditoria(OrigemAuditoria.AGENTE):
                conteudo = await self._chamar_tool(state["tenant_id"], nome, argumentos, permitir_acao=True)
        else:
            conteudo = json.dumps({"encontrado": False, "mensagem": MENSAGEM_ACAO_RECUSADA})

        mensagem_tool = {"role": "tool", "tool_call_id": tool_call_id, "name": nome, "content": conteudo}
        return {
            **state,
            "mensagens": [*state["mensagens"], mensagem_tool],
            "chamadas_tool": state["chamadas_tool"] + 1,
        }

    async def _chamar_tool(self, tenant_id: UUID, nome: str, argumentos: dict, *, permitir_acao: bool = False) -> str:
        spec = TOOLS_POR_NOME.get(nome)
        if spec is None:
            return json.dumps({"encontrado": False, "mensagem": f"Tool '{nome}' não existe."})
        if spec.acao and not permitir_acao:
            # Guarda de defesa em profundidade: mesmo que o roteamento do grafo
            # tenha um bug, o único ponto que de fato invoca a função da tool
            # nunca executa uma ação sem a flag setada pelo nó de confirmação.
            return json.dumps({"encontrado": False, "mensagem": f"Tool de ação '{nome}' requer confirmação explícita."})
        try:
            entrada = spec.input_model.model_validate(argumentos)
        except ValidationError:
            return json.dumps({"encontrado": False, "mensagem": f"Parâmetros inválidos para a tool '{nome}'."})
        saida = await spec.funcao(self.db, tenant_id, entrada)
        return saida.model_dump_json()

    async def _formatar_resposta(self, state: AgenteState) -> AgenteState:
        texto = (state["mensagens"][-1].get("content") or "").strip()
        return {**state, "resposta": texto or RESPOSTA_PADRAO_SEM_TEXTO}
