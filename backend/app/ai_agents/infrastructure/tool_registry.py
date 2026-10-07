"""Registro das tools de FASE9-IMPL-01 no formato de function-calling do LLM (FASE9-IMPL-02).

Cada `ToolSpec` liga o nome exposto ao modelo à função real em
`app.ai_agents.application.tools` e ao schema Pydantic que valida os
argumentos que o modelo propõe.
"""
from dataclasses import dataclass
from typing import Awaitable, Callable
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_agents.application import tools
from app.ai_agents.domain import schemas


@dataclass(frozen=True)
class ToolSpec:
    nome: str
    descricao: str
    input_model: type[BaseModel]
    funcao: Callable[[AsyncSession, UUID, BaseModel], Awaitable[BaseModel]]


TOOL_SPECS: list[ToolSpec] = [
    ToolSpec("consultar_lote", tools.consultar_lote.__doc__ or "", schemas.ConsultarLoteInput, tools.consultar_lote),
    ToolSpec("buscar_lotes", tools.buscar_lotes.__doc__ or "", schemas.BuscarLotesInput, tools.buscar_lotes),
    ToolSpec(
        "consultar_disponibilidade",
        tools.consultar_disponibilidade.__doc__ or "",
        schemas.ConsultarDisponibilidadeInput,
        tools.consultar_disponibilidade,
    ),
    ToolSpec("lotes_de_esquina", tools.lotes_de_esquina.__doc__ or "", schemas.LotesDeEsquinaInput, tools.lotes_de_esquina),
    ToolSpec("lotes_proximos_de", tools.lotes_proximos_de.__doc__ or "", schemas.LotesProximosDeInput, tools.lotes_proximos_de),
    ToolSpec("lotes_dentro_de", tools.lotes_dentro_de.__doc__ or "", schemas.LotesDentroDeInput, tools.lotes_dentro_de),
    ToolSpec(
        "distancia_entre_lotes",
        tools.distancia_entre_lotes.__doc__ or "",
        schemas.DistanciaEntreLotesInput,
        tools.distancia_entre_lotes,
    ),
    ToolSpec("consultar_clientes", tools.consultar_clientes.__doc__ or "", schemas.ConsultarClientesInput, tools.consultar_clientes),
    ToolSpec("consultar_corretores", tools.consultar_corretores.__doc__ or "", schemas.ConsultarCorretoresInput, tools.consultar_corretores),
    ToolSpec("consultar_vendas", tools.consultar_vendas.__doc__ or "", schemas.ConsultarVendasInput, tools.consultar_vendas),
    ToolSpec("buscar_documentos", tools.buscar_documentos.__doc__ or "", schemas.BuscarDocumentosInput, tools.buscar_documentos),
    ToolSpec(
        "consultar_condicoes_comerciais",
        tools.consultar_condicoes_comerciais.__doc__ or "",
        schemas.ConsultarCondicoesComerciaisInput,
        tools.consultar_condicoes_comerciais,
    ),
]

TOOLS_POR_NOME: dict[str, ToolSpec] = {spec.nome: spec for spec in TOOL_SPECS}


def specs_para_llm() -> list[dict]:
    """Formato de tool-calling aceito pelo Ollama (`POST /api/chat`, campo `tools`)."""
    return [
        {
            "type": "function",
            "function": {
                "name": spec.nome,
                "description": spec.descricao,
                "parameters": spec.input_model.model_json_schema(),
            },
        }
        for spec in TOOL_SPECS
    ]
