"""FastAPI application entry point."""
from fastapi import FastAPI
from app.config import Settings

settings = Settings()

app = FastAPI(
    title="Hope",
    description="Sistema SaaS multitenant para gestão de loteamentos e imóveis",
    version="0.1.0",
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
