"""Testes do endpoint de geração de resposta com citação de fonte (FASE7-IMPL-04/SCRUM-91)."""
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_rag.application.pergunta_service import RESPOSTA_SEM_CONTEXTO
from app.ai_rag.domain.models import DocumentChunk
from app.config import Settings
from app.documentos.domain.models import Documento
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant

_DIM = Settings().embedding_dimensions


def _vetor(valor: float) -> list[float]:
    return [valor] * _DIM


def _vetor_proximo(fracao_alinhada: float) -> list[float]:
    """Vetor com `fracao_alinhada` das dimensões iguais a 1.0 (resto 0.0) — ver test_ai_rag_busca.py."""
    n_alinhadas = round(_DIM * fracao_alinhada)
    return [1.0] * n_alinhadas + [0.0] * (_DIM - n_alinhadas)


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> tuple[str, Tenant]:
    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    db.add(tenant)
    await db.flush()

    user = User(email=f"{tenant_slug}@test.com", hashed_password=hash_password("senha123"), full_name="Test User")
    db.add(user)
    await db.flush()

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
    await db.commit()

    return create_access_token(user.id, tenant.id, Settings()), tenant


async def _criar_documento(db: AsyncSession, tenant: Tenant, nome: str) -> Documento:
    documento = Documento(
        tenant_id=tenant.id,
        nome=nome,
        content_type="text/plain",
        tamanho_bytes=10,
        storage_key=f"documentos/{tenant.id}/{nome}",
        status_indexacao="concluido",
    )
    db.add(documento)
    await db.commit()
    await db.refresh(documento)
    return documento


async def _criar_chunk(db: AsyncSession, documento: Documento, tenant: Tenant, texto: str, embedding: list[float]) -> DocumentChunk:
    chunk = DocumentChunk(
        documento_id=documento.id,
        tenant_id=tenant.id,
        ordem=0,
        texto=texto,
        embedding=embedding,
    )
    db.add(chunk)
    await db.commit()
    return chunk


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_perguntar_cita_documento_de_origem(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """Critério de aceite: para pergunta sobre documento conhecido, a resposta cita o documento de origem."""
    token, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-pergunta-fonte")
    documento = await _criar_documento(db_session, tenant, "memorial-descritivo.txt")
    await _criar_chunk(db_session, documento, tenant, "o loteamento possui 50 lotes", _vetor(1.0))

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = _vetor(1.0)
    mock_llm.generate.return_value = "O loteamento possui 50 lotes, segundo o memorial descritivo."
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        "/rag/perguntar", json={"pergunta": "quantos lotes tem o loteamento?"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["resposta"] == "O loteamento possui 50 lotes, segundo o memorial descritivo."
    assert len(body["fontes"]) == 1
    assert body["fontes"][0]["documento_id"] == str(documento.id)
    assert body["fontes"][0]["documento_nome"] == "memorial-descritivo.txt"

    prompt_enviado = mock_llm.generate.call_args.args[0]
    assert "o loteamento possui 50 lotes" in prompt_enviado
    assert "quantos lotes tem o loteamento?" in prompt_enviado


@pytest.mark.asyncio
async def test_perguntar_sem_contexto_relevante_nao_inventa(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """Critério de aceite: sem contexto relevante disponível, responde que não encontrou em vez de inventar."""
    token, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-pergunta-sem-contexto")
    documento = await _criar_documento(db_session, tenant, "memorial.txt")
    await _criar_chunk(db_session, documento, tenant, "texto totalmente não relacionado", _vetor_proximo(0.0))

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = _vetor_proximo(1.0)
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        "/rag/perguntar", json={"pergunta": "pergunta sem relação com os documentos"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["resposta"] == RESPOSTA_SEM_CONTEXTO
    assert body["fontes"] == []
    mock_llm.generate.assert_not_called()


@pytest.mark.asyncio
async def test_perguntar_nao_vaza_chunk_de_outro_tenant(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """A resposta gerada nunca cita documento de outro tenant."""
    token_a, tenant_a = await _criar_usuario_com_tenant(db_session, "tenant-rag-pergunta-a")
    token_b, tenant_b = await _criar_usuario_com_tenant(db_session, "tenant-rag-pergunta-b")

    documento_a = await _criar_documento(db_session, tenant_a, "memorial-a.txt")
    documento_b = await _criar_documento(db_session, tenant_b, "memorial-b.txt")
    await _criar_chunk(db_session, documento_a, tenant_a, "conteudo do tenant A", _vetor(1.0))
    await _criar_chunk(db_session, documento_b, tenant_b, "conteudo do tenant B", _vetor(1.0))

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = _vetor(1.0)
    mock_llm.generate.return_value = "resposta baseada no tenant A"
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        "/rag/perguntar", json={"pergunta": "qualquer pergunta"}, headers=_auth_headers(token_a)
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["fontes"]) == 1
    assert body["fontes"][0]["documento_id"] == str(documento_a.id)
