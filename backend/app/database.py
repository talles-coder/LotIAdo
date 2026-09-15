"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.common.models import Base

# Importados pelo efeito colateral, nesta ordem:
# 1. app.models — registra todos os domain models no declarative registry
#    do SQLAlchemy, para que relationship() por string (ex.: "Tenant")
#    resolva mesmo quando nada no caminho real da rota importa aquela
#    classe diretamente.
# 2. app.audit.infrastructure.tracking — registra o listener de auditoria
#    automática (`before_flush`) em toda Session da aplicação.
from app import models as _domain_models  # noqa: F401
from app.audit.infrastructure import tracking as _audit_tracking  # noqa: F401

settings = Settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncSession:
    """Dependency to get database session."""
    async with async_session() as session:
        yield session
