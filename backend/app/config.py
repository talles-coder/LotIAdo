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

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
