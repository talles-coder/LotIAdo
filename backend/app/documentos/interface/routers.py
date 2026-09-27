"""Documentos module HTTP routes."""
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_rag.infrastructure.queue import enfileirar_processamento_documento
from app.config import Settings
from app.documentos.application.documento_service import DocumentoService
from app.documentos.domain.exceptions import (
    DocumentoNaoEncontradoError,
    LoteamentoDoDocumentoNaoEncontradoError,
    LoteDoDocumentoNaoEncontradoError,
)
from app.documentos.infrastructure.storage import MinioStorage
from app.documentos.interface.schemas import DocumentoResponse, DocumentoUrlAssinadaResponse
from app.identity.interface.dependencies import get_current_tenant_id, get_settings, require_permission
from app.tenancy.interface.dependencies import get_tenant_scoped_db

router = APIRouter(tags=["documentos"])


def _service(db: AsyncSession, settings: Settings) -> DocumentoService:
    return DocumentoService(db, MinioStorage(settings))


@router.post("/documentos", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
async def enviar_documento(
    arquivo: UploadFile = File(...),
    tipo: str | None = Form(None),
    loteamento_id: UUID | None = Form(None),
    lote_id: UUID | None = Form(None),
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_permission("documentos:gerenciar")),
) -> DocumentoResponse:
    """Envia um documento (memorial, contrato, tabela de preços etc.) para o MinIO."""
    conteudo = await arquivo.read()
    service = _service(db, settings)
    try:
        documento = await service.upload(
            tenant_id,
            arquivo.filename or "documento",
            conteudo,
            arquivo.content_type or "application/octet-stream",
            tipo=tipo,
            loteamento_id=loteamento_id,
            lote_id=lote_id,
        )
    except LoteamentoDoDocumentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loteamento não encontrado")
    except LoteDoDocumentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lote não encontrado")

    # Enfileira o processamento (FASE7-IMPL-01) sem esperar o resultado — a
    # rota responde assim que o upload para o MinIO termina, conforme
    # critério de aceite do card.
    enfileirar_processamento_documento(documento.id, tenant_id, settings)

    return DocumentoResponse.model_validate(documento)


@router.get("/documentos", response_model=list[DocumentoResponse])
async def listar_documentos(
    loteamento_id: UUID | None = Query(None),
    lote_id: UUID | None = Query(None),
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    settings: Settings = Depends(get_settings),
) -> list[DocumentoResponse]:
    """Lista os documentos ativos do tenant, opcionalmente filtrados por loteamento/lote."""
    service = _service(db, settings)
    documentos = await service.listar(tenant_id, loteamento_id=loteamento_id, lote_id=lote_id)
    return [DocumentoResponse.model_validate(documento) for documento in documentos]


@router.get("/documentos/{documento_id}/url-assinada", response_model=DocumentoUrlAssinadaResponse)
async def obter_url_assinada_documento(
    documento_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    settings: Settings = Depends(get_settings),
) -> DocumentoUrlAssinadaResponse:
    """Gera uma URL assinada (válida por 1h) para download do documento."""
    service = _service(db, settings)
    try:
        url = await service.obter_url_assinada(tenant_id, documento_id)
    except DocumentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")
    return DocumentoUrlAssinadaResponse(url=url)


@router.delete("/documentos/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_documento(
    documento_id: UUID,
    tenant_id: UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_tenant_scoped_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(require_permission("documentos:gerenciar")),
) -> None:
    """Remove logicamente (soft-delete) um documento do tenant autenticado."""
    service = _service(db, settings)
    try:
        await service.remover(tenant_id, documento_id)
    except DocumentoNaoEncontradoError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado")
