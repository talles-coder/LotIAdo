"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from .env."""

    database_url: str = "postgresql+asyncpg://lotiado_app:lotiado_app@localhost:5432/lotiado"
    environment: str = "development"
    debug: bool = True

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    invitation_expire_hours: int = 168

    # Origens permitidas para o app Expo Web (navegador). Nativo n�o usa CORS.
    cors_origins: list[str] = ["http://localhost:8081", "http://localhost:19006"]

    # MinIO (S3-compatible). Backend roda no host (nao containerizado), entao
    # o endpoint padrao e `localhost` - igual ao `EXPO_PUBLIC_API_URL` do app
    # mobile (ver mobile/.env.example). `minio_public_endpoint_url` existe a
    # parte porque a URL assinada e consumida pelo cliente (navegador/app), nao
    # pelo backend: no emulador Android, por exemplo, precisa ser
    # `http://10.0.2.2:9000` em vez de `http://localhost:9000`.
    minio_endpoint_url: str = "http://localhost:9000"
    minio_public_endpoint_url: str | None = None
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    minio_bucket: str = "lotiado"

    # Redis (fila RQ) e Ollama (LLMProvider). Igual ao MinIO acima, o backend
    # roda no host por padrao, entao os defaults apontam para localhost; o
    # servico `worker` no docker-compose sobrescreve via env vars proprias
    # (nomes de servico da rede do compose).
    redis_url: str = "redis://localhost:6379/0"
    ollama_base_url: str = "http://localhost:11434"
    # D6 (docs/backlog/fase-7-documentos-rag.md): nomic-embed-text escolhido
    # como primeiro modelo de embeddings — 768 dimensoes, roda bem em CPU.
    # `embedding_dimensions` precisa bater com a coluna `vector` de
    # `document_chunks` (ver migration 20260927130000); trocar o modelo exige
    # nova migration se a dimensao mudar.
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_generation_model: str = "llama3.2"
    embedding_dimensions: int = 768

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
