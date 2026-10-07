"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.audit.interface.middleware import AuditContextMiddleware
from app.config import Settings
from app.observabilidade.infrastructure.logging_config import configurar_logging_estruturado
from app.observabilidade.interface.middleware import RequestIdMiddleware
from app.observabilidade.interface.routers import router as observabilidade_router
from app.ai_agents.interface.routers import router as ai_agents_router
from app.ai_rag.interface.routers import router as ai_rag_router
from app.clientes.interface.routers import router as clientes_router
from app.corretores.interface.routers import router as corretores_router
from app.documentos.interface.routers import router as documentos_router
from app.geo.interface.routers import router as geo_router
from app.identity.interface.routers import router as identity_router
from app.loteamentos_lotes.interface.routers import router as loteamentos_lotes_router
from app.vendas_reservas.interface.routers import router as vendas_reservas_router

settings = Settings()
configurar_logging_estruturado()

app = FastAPI(
    title="LotIAdo",
    description="Sistema SaaS multitenant para gestão de loteamentos e imóveis",
    version="0.1.0",
)

# Popula o usuário/tenant atual (via JWT) para toda request, para que a
# auditoria automática (app.audit.infrastructure.tracking) funcione sem
# nenhuma rota precisar declarar nada.
app.add_middleware(AuditContextMiddleware)
# Atribui um request_id por request, para correlacionar no log estruturado de
# IA (app.observabilidade) as várias chamadas de LLMProvider de uma mesma
# interação (ex.: RAG busca+gera, ou o agente decidindo em loop).
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(identity_router)
app.include_router(clientes_router)
app.include_router(corretores_router)
app.include_router(loteamentos_lotes_router)
app.include_router(documentos_router)
app.include_router(geo_router)
app.include_router(vendas_reservas_router)
app.include_router(ai_rag_router)
app.include_router(ai_agents_router)
app.include_router(observabilidade_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
