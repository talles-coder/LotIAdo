"""FastAPI application entry point."""
from fastapi import FastAPI
from app.config import Settings
from app.identity.interface.routers import router as identity_router

settings = Settings()

app = FastAPI(
    title="Hope",
    description="Sistema SaaS multitenant para gestão de loteamentos e imóveis",
    version="0.1.0",
)

app.include_router(identity_router)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
