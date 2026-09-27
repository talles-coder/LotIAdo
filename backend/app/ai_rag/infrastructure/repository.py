"""Database access for document_chunks."""
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_rag.domain.models import DocumentChunk


async def create_chunks(db: AsyncSession, chunks: list[DocumentChunk]) -> None:
    """Persist all chunks of a document in a single transaction."""
    db.add_all(chunks)
    await db.commit()


async def delete_chunks_by_documento(db: AsyncSession, tenant_id: UUID, documento_id: UUID) -> None:
    """Remove todos os chunks existentes de um documento (usado antes de reindexar)."""
    await db.execute(
        delete(DocumentChunk).where(
            DocumentChunk.documento_id == documento_id,
            DocumentChunk.tenant_id == tenant_id,
        )
    )
    await db.commit()
