"""Database access for the documentos module."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.documentos.domain.models import Documento


async def get_documento_by_id(db: AsyncSession, tenant_id: UUID, documento_id: UUID) -> Documento | None:
    """Fetch an active (non-removed) documento by id, scoped to the tenant."""
    result = await db.execute(
        select(Documento).where(
            Documento.id == documento_id,
            Documento.tenant_id == tenant_id,
            Documento.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def list_documentos(
    db: AsyncSession,
    tenant_id: UUID,
    loteamento_id: UUID | None = None,
    lote_id: UUID | None = None,
) -> list[Documento]:
    """List active documentos for the tenant, opcionalmente filtrados por loteamento/lote."""
    filtros = [Documento.tenant_id == tenant_id, Documento.deleted_at.is_(None)]
    if loteamento_id is not None:
        filtros.append(Documento.loteamento_id == loteamento_id)
    if lote_id is not None:
        filtros.append(Documento.lote_id == lote_id)

    result = await db.execute(select(Documento).where(*filtros))
    return list(result.scalars().all())


async def create_documento(db: AsyncSession, documento: Documento) -> Documento:
    """Persist a new documento.

    Sem `db.refresh()` de propósito — ver nota equivalente em
    app/loteamentos_lotes/infrastructure/repository.py.
    """
    db.add(documento)
    await db.commit()
    return documento


async def save_documento(db: AsyncSession, documento: Documento) -> Documento:
    """Persist changes made to an existing documento. Ver nota em `create_documento()`."""
    await db.commit()
    return documento
