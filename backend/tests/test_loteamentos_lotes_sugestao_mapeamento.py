"""Testes da sugestão automática de mapeamento de colunas do CSV via LLM (FASE8-IMPL-01/SCRUM-97)."""
import json
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> str:
    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    db.add(tenant)
    await db.flush()

    user = User(email=f"{tenant_slug}@test.com", hashed_password=hash_password("senha123"), full_name="Test User")
    db.add(user)
    await db.flush()

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
    await db.commit()

    return create_access_token(user.id, tenant.id, Settings())


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _criar_loteamento(client: AsyncClient, token: str) -> str:
    response = await client.post("/loteamentos", json={"nome": "Loteamento Teste"}, headers=_auth_headers(token))
    return response.json()["id"]


@pytest.mark.asyncio
async def test_sugerir_mapeamento_pre_preenche_campos_obvios(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Critério de aceite: colunas óbvias (ex.: 'Preço (R$)') são sugeridas para o campo correto."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-sugestao-mapeamento-ok")
    loteamento_id = await _criar_loteamento(client, token)

    resposta_llm = json.dumps(
        {
            "sugestoes": [
                {"campo": "identificacao", "coluna": "Identificação", "confianca": 0.95},
                {"campo": "quadra", "coluna": "Quadra", "confianca": 0.8},
                {"campo": "area_m2", "coluna": None, "confianca": 0.0},
                {"campo": "preco", "coluna": "Preço (R$)", "confianca": 0.9},
            ]
        }
    )
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = resposta_llm
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar/sugerir-mapeamento",
        json={"colunas": ["Identificação", "Quadra", "Preço (R$)"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    sugestoes = response.json()["sugestoes"]
    assert sugestoes["identificacao"] == {"coluna": "Identificação", "confianca": 0.95}
    assert sugestoes["quadra"] == {"coluna": "Quadra", "confianca": 0.8}
    assert sugestoes["preco"] == {"coluna": "Preço (R$)", "confianca": 0.9}
    assert "area_m2" not in sugestoes
    mock_llm.generate.assert_called_once()


@pytest.mark.asyncio
async def test_sugerir_mapeamento_ignora_coluna_inventada_pelo_llm(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Uma coluna sugerida que não existe no CSV enviado é descartada (defesa contra alucinação)."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-sugestao-mapeamento-alucinacao")
    loteamento_id = await _criar_loteamento(client, token)

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = json.dumps(
        {"sugestoes": [{"campo": "identificacao", "coluna": "Coluna Que Não Existe", "confianca": 0.9}]}
    )
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar/sugerir-mapeamento",
        json={"colunas": ["Identificação"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["sugestoes"] == {}


@pytest.mark.asyncio
async def test_sugerir_mapeamento_com_resposta_invalida_retorna_vazio_sem_quebrar(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Critério de aceite: uma falha do LLM nunca bloqueia o fluxo — cai para mapeamento manual."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-sugestao-mapeamento-invalida")
    loteamento_id = await _criar_loteamento(client, token)

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "não é json"
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar/sugerir-mapeamento",
        json={"colunas": ["Identificação"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["sugestoes"] == {}
    assert mock_llm.generate.call_count == 2


@pytest.mark.asyncio
async def test_sugerir_mapeamento_extrai_json_de_resposta_com_texto_ao_redor(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    """Modelos locais às vezes envolvem o JSON em texto extra; o serviço deve extrair só o objeto."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-sugestao-mapeamento-texto-extra")
    loteamento_id = await _criar_loteamento(client, token)

    mock_llm = AsyncMock()
    mock_llm.generate.return_value = (
        'Aqui está o mapeamento:\n{"sugestoes": [{"campo": "identificacao", "coluna": "ID", "confianca": 0.7}]}\nEspero ter ajudado!'
    )
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar/sugerir-mapeamento",
        json={"colunas": ["ID"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["sugestoes"]["identificacao"] == {"coluna": "ID", "confianca": 0.7}


@pytest.mark.asyncio
async def test_sugerir_mapeamento_loteamento_inexistente_retorna_404(
    client: AsyncClient, db_session: AsyncSession
):
    token = await _criar_usuario_com_tenant(db_session, "tenant-sugestao-mapeamento-404")

    response = await client.post(
        "/loteamentos/00000000-0000-0000-0000-000000000000/lotes/importar/sugerir-mapeamento",
        json={"colunas": ["Identificação"]},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404
