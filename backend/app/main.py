"""FastAPI application entry point."""
from fastapi import FastAPI
from app.audit.interface.middleware import AuditContextMiddleware
from app.config import Settings
from app.clientes.interface.routers import router as clientes_router
from app.corretores.interface.routers import router as corretores_router
from app.identity.interface.routers import router as identity_router
from app.loteamentos_lotes.interface.routers import router as loteamentos_lotes_router
from app.vendas_reservas.interface.routers import router as vendas_reservas_router

settings = Settings()

app = FastAPI(
    title="LotIAdo",
    description="Sistema SaaS multitenant para gestão de loteamentos e imóveis",
    version="0.1.0",
)

# Popula o usuário/tenant atual (via JWT) para toda request, para que a
# auditoria automática (app.audit.infrastructure.tracking) funcione sem
# nenhuma rota precisar declarar nada.
app.add_middleware(AuditContextMiddleware)

app.include_router(identity_router)
app.include_router(clientes_router)
app.include_router(corretores_router)
app.include_router(loteamentos_lotes_router)
app.include_router(vendas_reservas_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
