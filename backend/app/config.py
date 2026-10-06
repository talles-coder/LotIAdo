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

    # Origens permitidas para o app Expo Web (navegador). Nativo não usa CORS.
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

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
