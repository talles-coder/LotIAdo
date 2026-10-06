"""Testes do endpoint de busca semântica com filtro de escopo (FASE7-IMPL-03/SCRUM-90)."""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_rag.domain.models import DocumentChunk
from app.config import Settings
from app.documentos.domain.models import Documento
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.loteamentos_lotes.domain.models import Loteamento
from app.tenancy.domain.models import Tenant

_DIM = Settings().embedding_dimensions


def _vetor(valor: float) -> list[float]:
    return [valor] * _DIM


def _vetor_proximo(fracao_alinhada: float) -> list[float]:
    """Vetor com `fracao_alinhada` das dimensões iguais a 1.0 (resto 0.0).

    Cosseno é invariante a escala — usar vetores puramente escalares (ex.:
    `[0.5] * DIM` vs `[1.0] * DIM`) sempre dá similaridade 1.0 entre si. Variar
    a *direção* (quantas dimensões apontam para o mesmo lugar do vetor da
    pergunta, `[1.0] * DIM`) é o jeito de simular distâncias diferentes.
    """
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


async def _criar_documento(
    db: AsyncSession, tenant: Tenant, nome: str, loteamento_id=None
) -> Documento:
    documento = Documento(
        tenant_id=tenant.id,
        loteamento_id=loteamento_id,
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


async def _criar_chunk(
    db: AsyncSession, documento: Documento, tenant: Tenant, texto: str, embedding: list[float], loteamento_id=None
) -> DocumentChunk:
    chunk = DocumentChunk(
        documento_id=documento.id,
        tenant_id=tenant.id,
        loteamento_id=loteamento_id,
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
async def test_busca_nao_vaza_chunk_de_outro_tenant(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """Critério de aceite: a mesma pergunta nunca retorna chunk de outro tenant."""
    token_a, tenant_a = await _criar_usuario_com_tenant(db_session, "tenant-rag-busca-a")
    token_b, tenant_b = await _criar_usuario_com_tenant(db_session, "tenant-rag-busca-b")

    documento_a = await _criar_documento(db_session, tenant_a, "memorial-a.txt")
    documento_b = await _criar_documento(db_session, tenant_b, "memorial-b.txt")
    await _criar_chunk(db_session, documento_a, tenant_a, "conteudo do tenant A", _vetor(1.0))
    await _criar_chunk(db_session, documento_b, tenant_b, "conteudo do tenant B", _vetor(1.0))

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = _vetor(1.0)
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        "/rag/buscar", json={"pergunta": "qualquer pergunta"}, headers=_auth_headers(token_a)
    )

    assert response.status_code == 200
    resultados = response.json()
    assert len(resultados) == 1
    assert resultados[0]["documento_id"] == str(documento_a.id)
    assert resultados[0]["texto"] == "conteudo do tenant A"


@pytest.mark.asyncio
async def test_busca_retorna_top_k_ordenado_por_similaridade(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """Os chunks mais próximos do embedding da pergunta vêm primeiro, respeitando `top_k`."""
    token, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-busca-topk")
    documento = await _criar_documento(db_session, tenant, "memorial.txt")

    await _criar_chunk(db_session, documento, tenant, "pouco relevante", _vetor_proximo(0.1))
    await _criar_chunk(db_session, documento, tenant, "muito relevante", _vetor_proximo(1.0))
    await _criar_chunk(db_session, documento, tenant, "relevancia media", _vetor_proximo(0.5))

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = _vetor_proximo(1.0)
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        "/rag/buscar", json={"pergunta": "pergunta", "top_k": 2}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    resultados = response.json()
    assert len(resultados) == 2
    assert resultados[0]["texto"] == "muito relevante"
    assert resultados[0]["score"] > resultados[1]["score"]


@pytest.mark.asyncio
async def test_busca_filtra_por_loteamento(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """Informar `loteamento_id` restringe a busca aos chunks daquele loteamento."""
    token, tenant = await _criar_usuario_com_tenant(db_session, "tenant-rag-busca-loteamento")

    loteamento = Loteamento(tenant_id=tenant.id, nome="Loteamento Alvo")
    db_session.add(loteamento)
    await db_session.commit()
    await db_session.refresh(loteamento)

    documento_no_loteamento = await _criar_documento(
        db_session, tenant, "memorial-loteamento.txt", loteamento_id=loteamento.id
    )
    documento_fora = await _criar_documento(db_session, tenant, "memorial-geral.txt")

    await _criar_chunk(
        db_session, documento_no_loteamento, tenant, "sobre o loteamento", _vetor(1.0), loteamento_id=loteamento.id
    )
    await _criar_chunk(db_session, documento_fora, tenant, "documento geral", _vetor(1.0))

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = _vetor(1.0)
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        "/rag/buscar",
        json={"pergunta": "pergunta", "loteamento_id": str(loteamento.id)},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    resultados = response.json()
    assert len(resultados) == 1
    assert resultados[0]["documento_id"] == str(documento_no_loteamento.id)


@pytest.mark.asyncio
async def test_busca_com_loteamento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-rag-busca-404")

    response = await client.post(
        "/rag/buscar", json={"pergunta": "pergunta", "loteamento_id": str(uuid4())}, headers=_auth_headers(token)
    )

    assert response.status_code == 404
