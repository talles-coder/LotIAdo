"""Abstração `LLMProvider` (docs/02-arquitetura.md) sobre o Ollama.

`OllamaLLMProvider` é a única implementação por enquanto; outras (OpenAI,
Gemini, Bedrock) podem ser adicionadas depois sem tocar `ai_rag`/`ai_agents`,
que dependem só da interface `LLMProvider`.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx

from app.config import Settings


@dataclass
class ToolCall:
    """Uma chamada de tool decidida pelo modelo (FASE9-IMPL-02)."""

    id: str
    nome: str
    argumentos: dict


@dataclass
class ChatResposta:
    """Resultado de `LLMProvider.chat`: texto final e/ou tools que o modelo quer chamar."""

    conteudo: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(ABC):
    """Interface para geração de texto, embeddings e chat com tool calling via um modelo de LLM."""

    @abstractmethod
    async def embed(self, texto: str) -> list[float]:
        """Retorna o vetor de embedding de `texto`."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Retorna a resposta gerada para `prompt`."""

    @abstractmethod
    async def chat(self, mensagens: list[dict], tools: list[dict] | None = None) -> ChatResposta:
        """Chat multi-turno com tool calling opcional.

        `mensagens` no formato `{"role": ..., "content": ...}` (mensagens de
        papel "tool" incluem também `tool_call_id` e `name`). `tools` no
        formato de function-calling (`{"type": "function", "function": {...}}`).
        """


class OllamaLLMProvider(LLMProvider):
    """Implementação via API HTTP local do Ollama."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def embed(self, texto: str) -> list[float]:
        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=60.0) as client:
            response = await client.post(
                "/api/embeddings",
                json={"model": self.settings.ollama_embedding_model, "prompt": texto},
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=120.0) as client:
            response = await client.post(
                "/api/generate",
                json={"model": self.settings.ollama_generation_model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json()["response"]

    async def chat(self, mensagens: list[dict], tools: list[dict] | None = None) -> ChatResposta:
        payload: dict = {"model": self.settings.ollama_generation_model, "messages": mensagens, "stream": False}
        if tools:
            payload["tools"] = tools
        async with httpx.AsyncClient(base_url=self.settings.ollama_base_url, timeout=120.0) as client:
            response = await client.post("/api/chat", json=payload)
            response.raise_for_status()
            mensagem = response.json()["message"]
        tool_calls = [
            ToolCall(id=str(chamada.get("id", indice)), nome=chamada["function"]["name"], argumentos=chamada["function"]["arguments"])
            for indice, chamada in enumerate(mensagem.get("tool_calls") or [])
        ]
        return ChatResposta(conteudo=mensagem.get("content"), tool_calls=tool_calls)
