"""Documento use cases: upload, listagem/filtro, URL assinada e remoção."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.documentos.domain.exceptions import (
    DocumentoNaoEhImagemError,
    DocumentoNaoEncontradoError,
    LoteamentoDoDocumentoNaoEncontradoError,
    LoteDoDocumentoNaoEncontradoError,
)
from app.documentos.domain.models import Documento
from app.ai_rag.infrastructure.repository import delete_chunks_by_documento
from app.documentos.infrastructure.repository import (
    create_documento,
    get_documento_by_id,
    list_documentos,
    save_documento,
)
from app.documentos.infrastructure.storage import MinioStorage
from app.loteamentos_lotes.infrastructure.repository import get_lote_by_id, get_loteamento_by_id


class DocumentoService:
    """Orchestrates upload/armazenamento e consulta de documentos, escopados a um tenant."""

    def __init__(self, db: AsyncSession, storage: MinioStorage):
        self.db = db
        self.storage = storage

    async def upload(
        self,
        tenant_id: UUID,
        nome: str,
        conteudo: bytes,
        content_type: str,
        tipo: str | None = None,
        loteamento_id: UUID | None = None,
        lote_id: UUID | None = None,
    ) -> Documento:
        """Envia o arquivo para o MinIO e persiste os metadados no Postgres."""
        if loteamento_id is not None and await get_loteamento_by_id(self.db, tenant_id, loteamento_id) is None:
            raise LoteamentoDoDocumentoNaoEncontradoError()
        if lote_id is not None and await get_lote_by_id(self.db, tenant_id, lote_id) is None:
            raise LoteDoDocumentoNaoEncontradoError()

        documento_id = uuid4()
        storage_key = f"documentos/{tenant_id}/{documento_id}/{nome}"
        await self.storage.upload(storage_key, conteudo, content_type)

        documento = Documento(
            id=documento_id,
            tenant_id=tenant_id,
            loteamento_id=loteamento_id,
            lote_id=lote_id,
            nome=nome,
            tipo=tipo,
            content_type=content_type,
            tamanho_bytes=len(conteudo),
            storage_key=storage_key,
        )
        return await create_documento(self.db, documento)

    async def listar(
        self, tenant_id: UUID, loteamento_id: UUID | None = None, lote_id: UUID | None = None
    ) -> list[Documento]:
        """Lista documentos ativos do tenant, opcionalmente filtrados por loteamento/lote."""
        return await list_documentos(self.db, tenant_id, loteamento_id=loteamento_id, lote_id=lote_id)

    async def obter(self, tenant_id: UUID, documento_id: UUID) -> Documento:
        """Busca um documento ativo, levantando erro se não existir no tenant."""
        documento = await get_documento_by_id(self.db, tenant_id, documento_id)
        if documento is None:
            raise DocumentoNaoEncontradoError()
        return documento

    async def obter_url_assinada(self, tenant_id: UUID, documento_id: UUID) -> str:
        """Retorna uma URL assinada (válida por 1h) para download do documento."""
        documento = await self.obter(tenant_id, documento_id)
        return await self.storage.gerar_url_assinada(documento.storage_key)

    async def remover(self, tenant_id: UUID, documento_id: UUID) -> None:
        """Remove logicamente o documento (soft-delete); o objeto no MinIO é mantido."""
        documento = await self.obter(tenant_id, documento_id)
        documento.deleted_at = datetime.now(timezone.utc)
        await save_documento(self.db, documento)

    async def substituir(
        self, tenant_id: UUID, documento_id: UUID, nome: str, conteudo: bytes, content_type: str
    ) -> Documento:
        """Substitui o conteúdo de um documento existente (mesmo `storage_key`).

        Remove os `document_chunks` antigos antes de reenfileirar o
        reprocessamento (FASE7-IMPL-01) — a exclusão explícita aqui é
        redundante com o delete-then-insert que já roda dentro do job
        (idempotência), mas cumpre o critério de aceite do card de não
        deixar chunks órfãos entre a substituição e a conclusão do job.
        """
        documento = await self.obter(tenant_id, documento_id)
        await self.storage.upload(documento.storage_key, conteudo, content_type)

        documento.nome = nome
        documento.content_type = content_type
        documento.tamanho_bytes = len(conteudo)
        documento.status_indexacao = "pendente"
        await save_documento(self.db, documento)

        await delete_chunks_by_documento(self.db, tenant_id, documento_id)
        return documento

    async def solicitar_extracao_imagem(self, tenant_id: UUID, documento_id: UUID) -> Documento:
        """Marca o documento para a sugestão de extração (OCR + contornos, FASE8-IMPL-02).

        Quem efetivamente enfileira o job é a rota (`app/documentos/infrastructure/queue.py`) —
        este método só valida e reseta o estado, mesma divisão de responsabilidade do upload.
        """
        documento = await self.obter(tenant_id, documento_id)
        if not documento.content_type.startswith("image/"):
            raise DocumentoNaoEhImagemError()
        documento.status_extracao_imagem = "pendente"
        documento.resultado_extracao_imagem = None
        return await save_documento(self.db, documento)
