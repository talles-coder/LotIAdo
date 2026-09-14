"""FastAPI application entry point."""
from fastapi import FastAPI
from app.audit.interface.middleware import AuditContextMiddleware
from app.config import Settings
from app.identity.interface.routers import router as identity_router

settings = Settings()

app = FastAPI(
    title="Hope",
    description="Sistema SaaS multitenant para gestão de loteamentos e imóveis",
    version="0.1.0",
)

# Popula o usuário/tenant atual (via JWT) para toda request, para que a
# auditoria automática (app.audit.infrastructure.tracking) funcione sem
# nenhuma rota precisar declarar nada.
app.add_middleware(AuditContextMiddleware)

app.include_router(identity_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
