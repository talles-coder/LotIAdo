"""Database access for document_chunks."""
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


async def buscar_chunks_similares(
    db: AsyncSession,
    tenant_id: UUID,
    embedding: list[float],
    top_k: int,
    loteamento_id: UUID | None = None,
    lote_id: UUID | None = None,
) -> list[tuple[DocumentChunk, float]]:
    """Retorna os `top_k` chunks mais próximos de `embedding` (distância de cosseno).

    `tenant_id` é filtrado explicitamente aqui, além da RLS já ativa na sessão
    (`get_tenant_scoped_db`) — defesa em profundidade para queries vetoriais
    conforme CLAUDE.md e critério de aceite do FASE7-IMPL-03.
    """
    distancia = DocumentChunk.embedding.cosine_distance(embedding)
    query = (
        select(DocumentChunk, distancia.label("distancia"))
        .options(selectinload(DocumentChunk.documento))
        .where(DocumentChunk.tenant_id == tenant_id)
    )
    if loteamento_id is not None:
        query = query.where(DocumentChunk.loteamento_id == loteamento_id)
    if lote_id is not None:
        query = query.where(DocumentChunk.lote_id == lote_id)
    query = query.order_by(distancia).limit(top_k)

    result = await db.execute(query)
    return [(chunk, 1 - float(distancia)) for chunk, distancia in result.all()]
