"""Abstração `LLMProvider` (docs/02-arquitetura.md) sobre o Ollama.

`OllamaLLMProvider` é a única implementação por enquanto; outras (OpenAI,
Gemini, Bedrock) podem ser adicionadas depois sem tocar `ai_rag`/`ai_agents`,
que dependem só da interface `LLMProvider`.
"""
from abc import ABC, abstractmethod

import httpx

from app.config import Settings


class LLMProvider(ABC):
    """Interface para geração de texto e embeddings via um modelo de LLM."""

    @abstractmethod
    async def embed(self, texto: str) -> list[float]:
        """Retorna o vetor de embedding de `texto`."""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Retorna a resposta gerada para `prompt`."""


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
