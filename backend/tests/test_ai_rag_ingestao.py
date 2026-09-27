"""Testes do pipeline de ingestão (chunking + embeddings, FASE7-IMPL-01/SCRUM-88)."""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_rag.application.ingestao_service import _processar_documento_async
from app.ai_rag.domain.models import DocumentChunk
from app.config import Settings
from app.documentos.domain.models import Documento
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> tuple[str, "Tenant"]:
    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    db.add(tenant)
    await db.flush()

    user = User(email=f"{tenant_slug}@test.com", hashed_password=hash_password("senha123"), full_name="Test User")
    db.add(user)
    await db.flush()

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
    await db.commit()

    return create_access_token(user.id, tenant.id, Settings()), tenant


async def _criar_documento(db: AsyncSession, tenant: Tenant, storage_key: str) -> Documento:
    documento = Documento(
        tenant_id=tenant.id,
        nome="memorial.txt",
        content_type="text/plain",
        tamanho_bytes=100,
        storage_key=storage_key,
    )
    db.add(documento)
    await db.commit()
    await db.refresh(documento)
    return documento


@pytest.mark.asyncio
async def test_processar_documento_gera_chunks_com_embeddings(db_session: AsyncSession, monkeypatch):
    """Ao processar um documento, seus chunks são persistidos com embedding e escopo corretos."""
    _, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-ingestao")
    documento = await _criar_documento(db_session, tenant, storage_key="documentos/teste/memorial.txt")

    texto_documento = "Parágrafo um sobre o loteamento. " * 60
    monkeypatch.setattr(
        "app.ai_rag.application.ingestao_service.MinioStorage.baixar",
        AsyncMock(return_value=texto_documento.encode("utf-8")),
    )
    mock_llm = AsyncMock()
    mock_llm.embed.return_value = [0.1] * Settings().embedding_dimensions
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    async def _fake_session():
        yield db_session

    import contextlib

    monkeypatch.setattr(
        "app.ai_rag.application.ingestao_service.async_session",
        lambda: contextlib.nullcontext(db_session),
    )

    await _processar_documento_async(str(documento.id), str(tenant.id))

    await db_session.refresh(documento)
    assert documento.status_indexacao == "concluido"

    chunks = (
        await db_session.execute(select(DocumentChunk).where(DocumentChunk.documento_id == documento.id))
    ).scalars().all()
    assert len(chunks) > 1
    assert all(chunk.tenant_id == tenant.id for chunk in chunks)
    assert all(len(chunk.embedding) == Settings().embedding_dimensions for chunk in chunks)
    assert mock_llm.embed.await_count == len(chunks)


@pytest.mark.asyncio
async def test_processar_documento_marca_falhou_quando_erro(db_session: AsyncSession, monkeypatch):
    """Uma falha no meio do pipeline marca o documento como `falhou` em vez de deixar `processando` preso."""
    _, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-falha")
    documento = await _criar_documento(db_session, tenant, storage_key="documentos/teste/quebrado.txt")

    monkeypatch.setattr(
        "app.ai_rag.application.ingestao_service.MinioStorage.baixar",
        AsyncMock(side_effect=RuntimeError("MinIO indisponível")),
    )

    import contextlib

    monkeypatch.setattr(
        "app.ai_rag.application.ingestao_service.async_session",
        lambda: contextlib.nullcontext(db_session),
    )

    with pytest.raises(RuntimeError):
        await _processar_documento_async(str(documento.id), str(tenant.id))

    await db_session.refresh(documento)
    assert documento.status_indexacao == "falhou"


@pytest.mark.asyncio
async def test_processar_documento_reindexacao_nao_duplica_chunks(db_session: AsyncSession, monkeypatch):
    """Reprocessar o mesmo documento substitui os chunks antigos em vez de duplicá-los (FASE7-IMPL-02)."""
    _, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-reindexacao")
    documento = await _criar_documento(db_session, tenant, storage_key="documentos/teste/memorial.txt")

    monkeypatch.setattr(
        "app.ai_rag.application.ingestao_service.MinioStorage.baixar",
        AsyncMock(return_value=b"Um texto curto de teste."),
    )
    mock_llm = AsyncMock()
    mock_llm.embed.return_value = [0.1] * Settings().embedding_dimensions
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    import contextlib

    monkeypatch.setattr(
        "app.ai_rag.application.ingestao_service.async_session",
        lambda: contextlib.nullcontext(db_session),
    )

    await _processar_documento_async(str(documento.id), str(tenant.id))
    await _processar_documento_async(str(documento.id), str(tenant.id))

    chunks = (
        await db_session.execute(select(DocumentChunk).where(DocumentChunk.documento_id == documento.id))
    ).scalars().all()
    assert len(chunks) == 1


@pytest.mark.asyncio
async def test_processar_documento_inexistente_nao_levanta_erro(db_session: AsyncSession, monkeypatch):
    """Um `documento_id` que não existe (ex.: removido entre o enfileiramento e o processamento) é ignorado."""
    _, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-inexistente")

    import contextlib

    monkeypatch.setattr(
        "app.ai_rag.application.ingestao_service.async_session",
        lambda: contextlib.nullcontext(db_session),
    )

    await _processar_documento_async(str(uuid4()), str(tenant.id))
