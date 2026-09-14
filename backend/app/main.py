"""FastAPI application entry point."""
from fastapi import FastAPI
from app.config import Settings
from app.clientes.interface.routers import router as clientes_router
from app.corretores.interface.routers import router as corretores_router
from app.identity.interface.routers import router as identity_router
from app.loteamentos_lotes.interface.routers import router as loteamentos_lotes_router

settings = Settings()

app = FastAPI(
    title="Hope",
    description="Sistema SaaS multitenant para gestão de loteamentos e imóveis",
    version="0.1.0",
)

app.include_router(identity_router)
app.include_router(clientes_router)
app.include_router(corretores_router)
app.include_router(loteamentos_lotes_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
