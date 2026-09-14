"""Database configuration and session management."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import Settings
from app.common.models import Base

# Importados por efeito colateral: garante que todas as entidades estejam
# registradas no registry do SQLAlchemy antes da primeira query, já que
# relationships como `relationship("Tenant")` são resolvidos por nome de
# classe e falham se o módulo dono da classe nunca foi importado.
from app.tenancy.domain.models import Tenant  # noqa: F401
from app.identity.domain.models import User, UserTenantMembership  # noqa: F401
from app.clientes.domain.models import Cliente  # noqa: F401
from app.corretores.domain.models import Corretor  # noqa: F401
from app.loteamentos_lotes.domain.models import Loteamento, Lote  # noqa: F401

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
