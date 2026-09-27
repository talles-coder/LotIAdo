"""Módulo ai_rag: ingestão de documentos (chunking + embeddings) e busca semântica.

`llm_provider` é exposto aqui (em vez de instanciado por request, como
`MinioStorage`) porque é usado tanto pelas rotas HTTP quanto pelo worker RQ
(processo separado, sem ciclo de dependências do FastAPI) — ver
app/ai_rag/application/ingestao_service.py. Testes trocam a implementação via
`monkeypatch.setattr("app.ai_rag.llm_provider", ...)` (ver skill `testing`).
"""
from app.ai_rag.infrastructure.llm_provider import LLMProvider, OllamaLLMProvider
from app.config import Settings

llm_provider: LLMProvider = OllamaLLMProvider(Settings())
