"""Testes de integração do módulo documentos (upload, filtro, URL assinada)."""
import httpx
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> str:
    """Cria um usuário com membership em um tenant e retorna o token JWT."""
    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    db.add(tenant)
    await db.flush()

    user = User(
        email=f"{tenant_slug}@test.com",
        hashed_password=hash_password("senha123"),
        full_name="Test User",
    )
    db.add(user)
    await db.flush()

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
    await db.commit()

    return create_access_token(user.id, tenant.id, Settings())


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _criar_loteamento(client: AsyncClient, token: str, nome: str = "Loteamento Teste") -> str:
    response = await client.post("/loteamentos", json={"nome": nome}, headers=_auth_headers(token))
    return response.json()["id"]


async def _enviar_documento(
    client: AsyncClient,
    token: str,
    nome_arquivo: str = "memorial.pdf",
    loteamento_id: str | None = None,
    lote_id: str | None = None,
) -> dict:
    data = {}
    if loteamento_id is not None:
        data["loteamento_id"] = loteamento_id
    if lote_id is not None:
        data["lote_id"] = lote_id

    response = await client.post(
        "/documentos",
        files={"arquivo": (nome_arquivo, b"%PDF-1.4 conteudo de teste", "application/pdf")},
        data=data,
        headers=_auth_headers(token),
    )
    return response.json() if response.status_code == 201 else response.json() | {"_status": response.status_code}


@pytest.mark.asyncio
async def test_enviar_documento_e_recuperavel_via_url_assinada(client: AsyncClient, db_session: AsyncSession):
    """Um PDF enviado é recuperável via URL assinada (critério de aceite SCRUM-77)."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-documentos-upload")

    enviado = await client.post(
        "/documentos",
        files={"arquivo": ("memorial.pdf", b"%PDF-1.4 conteudo de teste", "application/pdf")},
        data={},
        headers=_auth_headers(token),
    )
    assert enviado.status_code == 201
    body = enviado.json()
    assert body["nome"] == "memorial.pdf"
    assert body["content_type"] == "application/pdf"
    documento_id = body["id"]

    url_response = await client.get(f"/documentos/{documento_id}/url-assinada", headers=_auth_headers(token))
    assert url_response.status_code == 200
    url = url_response.json()["url"]

    async with httpx.AsyncClient() as http:
        baixado = await http.get(url)
    assert baixado.status_code == 200
    assert baixado.content == b"%PDF-1.4 conteudo de teste"


@pytest.mark.asyncio
async def test_enviar_documento_enfileira_processamento_e_fica_pendente(client: AsyncClient, db_session: AsyncSession):
    """Upload enfileira o job de ingestão (SCRUM-88) sem bloquear a resposta, status inicial `pendente`."""
    from app.ai_rag.infrastructure.queue import NOME_FILA
    from app.config import Settings
    import redis
    from rq import Queue

    token = await _criar_usuario_com_tenant(db_session, "tenant-documentos-fila")
    fila = Queue(NOME_FILA, connection=redis.from_url(Settings().redis_url))
    fila.empty()

    body = await _enviar_documento(client, token)

    assert body["status_indexacao"] == "pendente"
    assert fila.count == 1


@pytest.mark.asyncio
async def test_listar_documentos_filtra_por_loteamento(client: AsyncClient, db_session: AsyncSession):
    """Filtro por loteamento retorna somente os documentos vinculados a ele."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-documentos-filtro")
    loteamento_a = await _criar_loteamento(client, token, nome="Loteamento A")
    loteamento_b = await _criar_loteamento(client, token, nome="Loteamento B")

    await _enviar_documento(client, token, nome_arquivo="doc-a.pdf", loteamento_id=loteamento_a)
    await _enviar_documento(client, token, nome_arquivo="doc-b.pdf", loteamento_id=loteamento_b)
    await _enviar_documento(client, token, nome_arquivo="doc-sem-vinculo.pdf")

    response = await client.get("/documentos", params={"loteamento_id": loteamento_a}, headers=_auth_headers(token))

    assert response.status_code == 200
    nomes = {documento["nome"] for documento in response.json()}
    assert nomes == {"doc-a.pdf"}


@pytest.mark.asyncio
async def test_listar_documentos_isola_por_tenant(client: AsyncClient, db_session: AsyncSession):
    """Um tenant não vê documentos enviados por outro tenant."""
    token_a = await _criar_usuario_com_tenant(db_session, "tenant-documentos-a")
    token_b = await _criar_usuario_com_tenant(db_session, "tenant-documentos-b")

    await _enviar_documento(client, token_a)

    response = await client.get("/documentos", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_enviar_documento_com_loteamento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Vincular um documento a um loteamento inexistente (ou de outro tenant) é rejeitado."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-documentos-loteamento-invalido")

    resultado = await _enviar_documento(client, token, loteamento_id="00000000-0000-0000-0000-000000000000")

    assert resultado["_status"] == 404


@pytest.mark.asyncio
async def test_remover_documento_e_remocao_logica(client: AsyncClient, db_session: AsyncSession):
    """Remover um documento é lógico: some da listagem mas não é hard-delete."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-documentos-remover")
    documento = await _enviar_documento(client, token)

    remocao = await client.delete(f"/documentos/{documento['id']}", headers=_auth_headers(token))
    assert remocao.status_code == 204

    listagem = await client.get("/documentos", headers=_auth_headers(token))
    assert listagem.json() == []


@pytest.mark.asyncio
async def test_substituir_documento_atualiza_metadados_e_volta_a_pendente(
    client: AsyncClient, db_session: AsyncSession
):
    """Substituir um documento sobrescreve o conteúdo no MinIO e reseta o status de indexação."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-documentos-substituir")
    documento = await _enviar_documento(client, token)

    substituicao = await client.put(
        f"/documentos/{documento['id']}",
        files={"arquivo": ("memorial-v2.pdf", b"%PDF-1.4 conteudo atualizado", "application/pdf")},
        headers=_auth_headers(token),
    )

    assert substituicao.status_code == 200
    body = substituicao.json()
    assert body["id"] == documento["id"]
    assert body["nome"] == "memorial-v2.pdf"
    assert body["status_indexacao"] == "pendente"

    url_response = await client.get(f"/documentos/{documento['id']}/url-assinada", headers=_auth_headers(token))
    async with httpx.AsyncClient() as http:
        baixado = await http.get(url_response.json()["url"])
    assert baixado.content == b"%PDF-1.4 conteudo atualizado"


@pytest.mark.asyncio
async def test_substituir_documento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Substituir um `documento_id` que não existe (ou de outro tenant) é rejeitado."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-documentos-substituir-404")

    resultado = await client.put(
        "/documentos/00000000-0000-0000-0000-000000000000",
        files={"arquivo": ("memorial.pdf", b"%PDF-1.4", "application/pdf")},
        headers=_auth_headers(token),
    )

    assert resultado.status_code == 404


@pytest.mark.asyncio
async def test_substituir_documento_duas_vezes_nao_acumula_chunks(client: AsyncClient, db_session: AsyncSession):
    """Substituir um documento duas vezes seguidas nunca acumula chunks (critério de aceite SCRUM-89)."""
    import contextlib
    from unittest.mock import AsyncMock

    import app.ai_rag as ai_rag
    from app.ai_rag.application.ingestao_service import _processar_documento_async
    from app.ai_rag.domain.models import DocumentChunk
    from app.identity.application.security import create_access_token, hash_password
    from app.identity.domain.models import User, UserTenantMembership
    from app.tenancy.domain.models import Tenant
    from sqlalchemy import select

    tenant = Tenant(name="tenant-documentos-reindexacao", slug="tenant-documentos-reindexacao")
    db_session.add(tenant)
    await db_session.flush()
    user = User(email="tenant-documentos-reindexacao@test.com", hashed_password=hash_password("senha123"), full_name="Test User")
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
    await db_session.commit()
    token = create_access_token(user.id, tenant.id, Settings())

    documento = await _enviar_documento(client, token)

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = [0.1] * Settings().embedding_dimensions

    for texto in (b"Um texto curto de teste.", b"Um texto diferente na segunda substituicao."):
        substituicao = await client.put(
            f"/documentos/{documento['id']}",
            files={"arquivo": ("v.txt", texto, "text/plain")},
            headers=_auth_headers(token),
        )
        assert substituicao.status_code == 200

        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(
                "app.ai_rag.application.ingestao_service.MinioStorage.baixar", AsyncMock(return_value=texto)
            )
            mp.setattr(ai_rag, "llm_provider", mock_llm)
            mp.setattr(
                "app.ai_rag.application.ingestao_service.async_session",
                lambda: contextlib.nullcontext(db_session),
            )
            await _processar_documento_async(documento["id"], str(tenant.id))

    chunks = (
        await db_session.execute(select(DocumentChunk).where(DocumentChunk.documento_id == documento["id"]))
    ).scalars().all()
    assert len(chunks) == 1
