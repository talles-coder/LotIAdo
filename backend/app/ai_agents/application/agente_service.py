"""Grafo do agente conversacional (FASE9-IMPL-02).

`StateGraph` (LangGraph) com três papéis: decisão (LLM com tool calling via
`LLMProvider.chat`), execução da(s) tool(s) escolhida(s) e formatação da
resposta final. O laço decidir -> executar_tool -> decidir se repete até o
modelo responder sem propor nova tool (ou até `MAX_CHAMADAS_TOOL`, para não
travar em loop). O agente nunca inventa dado: quando uma tool retorna
"não encontrado", isso vira uma mensagem de tool normal, e é o próprio modelo
quem comunica a ausência de resultado ao usuário (reforçado pelo `SYSTEM_PROMPT`).
"""
import json
from typing import TypedDict
from uuid import UUID

from langgraph.graph import END, StateGraph
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_agents.infrastructure.tool_registry import TOOLS_POR_NOME, specs_para_llm

MAX_CHAMADAS_TOOL = 5

SYSTEM_PROMPT = (
    "Você é o assistente do LotIAdo, um sistema de gestão de loteamentos. "
    "Responda em português usando as tools disponíveis para consultar dados reais — "
    "nunca invente lotes, preços, clientes ou qualquer outro dado. "
    "Se uma tool indicar que não encontrou o que foi pedido, informe isso ao "
    "usuário em vez de supor um resultado."
)

RESPOSTA_PADRAO_SEM_TEXTO = "Não consegui gerar uma resposta para essa pergunta."


class AgenteState(TypedDict):
    tenant_id: UUID
    mensagens: list[dict]
    chamadas_tool: int
    resposta: str


class AgenteService:
    """Orquestra o grafo do agente sobre uma sessão de banco já escopada ao tenant."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._grafo = self._construir_grafo()

    async def perguntar(self, tenant_id: UUID, pergunta: str) -> str:
        estado_inicial: AgenteState = {
            "tenant_id": tenant_id,
            "mensagens": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": pergunta},
            ],
            "chamadas_tool": 0,
            "resposta": "",
        }
        estado_final = await self._grafo.ainvoke(estado_inicial)
        return estado_final["resposta"]

    def _construir_grafo(self):
        grafo = StateGraph(AgenteState)
        grafo.add_node("decidir", self._decidir)
        grafo.add_node("executar_tool", self._executar_tool)
        grafo.add_node("formatar_resposta", self._formatar_resposta)
        grafo.set_entry_point("decidir")
        grafo.add_conditional_edges(
            "decidir",
            self._precisa_de_tool,
            {"tool": "executar_tool", "resposta": "formatar_resposta"},
        )
        grafo.add_edge("executar_tool", "decidir")
        grafo.add_edge("formatar_resposta", END)
        return grafo.compile()

    async def _decidir(self, state: AgenteState) -> AgenteState:
        resposta = await ai_rag.llm_provider.chat(state["mensagens"], tools=specs_para_llm())
        mensagem_assistente: dict = {"role": "assistant", "content": resposta.conteudo or ""}
        if resposta.tool_calls:
            mensagem_assistente["tool_calls"] = [
                {"id": chamada.id, "function": {"name": chamada.nome, "arguments": chamada.argumentos}}
                for chamada in resposta.tool_calls
            ]
        return {**state, "mensagens": [*state["mensagens"], mensagem_assistente]}

    def _precisa_de_tool(self, state: AgenteState) -> str:
        ultima = state["mensagens"][-1]
        if ultima.get("tool_calls") and state["chamadas_tool"] < MAX_CHAMADAS_TOOL:
            return "tool"
        return "resposta"

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

    async def _chamar_tool(self, tenant_id: UUID, nome: str, argumentos: dict) -> str:
        spec = TOOLS_POR_NOME.get(nome)
        if spec is None:
            return json.dumps({"encontrado": False, "mensagem": f"Tool '{nome}' não existe."})
        try:
            entrada = spec.input_model.model_validate(argumentos)
        except ValidationError:
            return json.dumps({"encontrado": False, "mensagem": f"Parâmetros inválidos para a tool '{nome}'."})
        saida = await spec.funcao(self.db, tenant_id, entrada)
        return saida.model_dump_json()

    async def _formatar_resposta(self, state: AgenteState) -> AgenteState:
        texto = (state["mensagens"][-1].get("content") or "").strip()
        return {**state, "resposta": texto or RESPOSTA_PADRAO_SEM_TEXTO}
