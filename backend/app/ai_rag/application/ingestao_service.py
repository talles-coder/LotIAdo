"""Pipeline de ingestão de documentos: chunking + embeddings, via job RQ.

`processar_documento` é o job enfileirado por
`app.ai_rag.infrastructure.queue.enfileirar_processamento_documento` e
consumido pelo worker (`app/worker.py`, processo separado do backend). RQ
executa jobs de forma síncrona — por isso a função síncrona faz
`asyncio.run()` sobre a lógica assíncrona (mesmo padrão de sessão async do
resto do app).

`tenant_id` viaja como argumento do job (em vez de ser descoberto a partir do
`documento_id` dentro do worker) de propósito: a tabela `documentos` tem RLS
(FORCE ROW LEVEL SECURITY) e o worker usa o mesmo papel de banco não-superusuário
da API (`lotiado_app`) — sem `app.tenant_id` já setado, nem o SELECT inicial
do documento enxergaria a linha. Quem enfileira (a rota de upload) já tem o
tenant autenticado, então não há por que descobri-lo de novo aqui.
"""
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

# `import app.ai_rag as ai_rag` (em vez de `from app.ai_rag import llm_provider`)
# de propósito: mantém a busca do atributo em tempo de chamada, para que
# `monkeypatch.setattr("app.ai_rag.llm_provider", ...)` (ver skill `testing`)
# realmente troque o provider usado aqui — um `from import` capturaria o
# valor antigo no momento do import deste módulo.
import app.ai_rag as ai_rag
from app.ai_rag.domain.models import DocumentChunk
from app.ai_rag.infrastructure.chunking import dividir_em_chunks
from app.ai_rag.infrastructure.repository import create_chunks, delete_chunks_by_documento
from app.config import Settings
from app.database import async_session
from app.documentos.domain.models import Documento
from app.documentos.infrastructure.storage import MinioStorage
from app.observabilidade.domain.chamada_ia import OrigemChamadaIA
from app.observabilidade.infrastructure.context import contexto_origem_ia


async def _set_tenant(db: AsyncSession, tenant_id: UUID) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})


async def _buscar_documento(db: AsyncSession, tenant_id: UUID, documento_id: UUID) -> Documento | None:
    await _set_tenant(db, tenant_id)
    result = await db.execute(
        select(Documento).where(Documento.id == documento_id, Documento.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def _marcar_status(db: AsyncSession, documento: Documento, status: str) -> None:
    documento.status_indexacao = status
    await db.commit()


async def _processar_documento_async(documento_id: str, tenant_id: str) -> None:
    settings = Settings()
    documento_uuid = UUID(documento_id)
    tenant_uuid = UUID(tenant_id)

    async with async_session() as db:
        documento = await _buscar_documento(db, tenant_uuid, documento_uuid)
        if documento is None:
            return

        await _marcar_status(db, documento, "processando")

        try:
            conteudo = await MinioStorage(settings).baixar(documento.storage_key)
            texto = conteudo.decode("utf-8", errors="ignore")
            chunks_texto = dividir_em_chunks(texto)

            chunks = []
            for ordem, chunk_texto in enumerate(chunks_texto):
                with contexto_origem_ia(OrigemChamadaIA.IMPORTACAO):
                    embedding = await ai_rag.llm_provider.embed(chunk_texto)
                chunks.append(
                    DocumentChunk(
                        documento_id=documento.id,
                        tenant_id=documento.tenant_id,
                        loteamento_id=documento.loteamento_id,
                        lote_id=documento.lote_id,
                        ordem=ordem,
                        texto=chunk_texto,
                        embedding=embedding,
                    )
                )

            await delete_chunks_by_documento(db, tenant_uuid, documento.id)
            if chunks:
                await create_chunks(db, chunks)

            await _marcar_status(db, documento, "concluido")
        except Exception:
            await _marcar_status(db, documento, "falhou")
            raise


def processar_documento(documento_id: str, tenant_id: str) -> None:
    """Job RQ: chunk + embed um documento e persiste em `document_chunks`."""
    import asyncio

    asyncio.run(_processar_documento_async(documento_id, tenant_id))
