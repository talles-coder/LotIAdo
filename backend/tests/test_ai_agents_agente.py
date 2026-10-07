"""Testes do grafo do agente (FASE9-IMPL-02/SCRUM-104): decisão -> tool -> resposta.

O LLM (`ai_rag.llm_provider.chat`) é mockado — o que se testa é a orquestração
do grafo (LangGraph) e a execução real das tools sobre dados de teste
conhecidos, não a qualidade do modelo em si.
"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from geoalchemy2.shape import from_shape
from httpx import AsyncClient
from shapely.geometry import LineString, box
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_rag.infrastructure.llm_provider import ChatResposta, ToolCall
from app.ai_agents.application.agente_service import RESPOSTA_PADRAO_SEM_TEXTO, AgenteService
from app.geo.domain.models import FeicaoReferencia, TipoFeicao
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.loteamentos_lotes.domain.models import Lote, Loteamento
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.config import Settings
from app.tenancy.domain.models import Tenant


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


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_agente_chama_tool_e_formata_resposta_final(db_session: AsyncSession, monkeypatch):
    """A pergunta de exemplo do briefing ('lotes disponíveis > 200m² em esquina') resolve via `lotes_de_esquina`."""
    tenant = Tenant(name="agente-esquina", slug="agente-esquina")
    db_session.add(tenant)
    await db_session.flush()
    loteamento = Loteamento(tenant_id=tenant.id, nome="Loteamento Teste")
    db_session.add(loteamento)
    await db_session.flush()
    lote = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="L-Esquina",
        status=LoteStatus.DISPONIVEL, area_m2=250,
        geometria=from_shape(box(0, 0, 0.001, 0.001), srid=4326),
    )
    db_session.add(lote)
    db_session.add_all(
        [
            FeicaoReferencia(
                tenant_id=tenant.id, loteamento_id=loteamento.id, tipo=TipoFeicao.RUA, nome="Rua A",
                geometria=from_shape(LineString([(-0.001, 0), (0.002, 0)]), srid=4326),
            ),
            FeicaoReferencia(
                tenant_id=tenant.id, loteamento_id=loteamento.id, tipo=TipoFeicao.RUA, nome="Rua B",
                geometria=from_shape(LineString([(0, -0.001), (0, 0.002)]), srid=4326),
            ),
        ]
    )
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.chat.side_effect = [
        ChatResposta(
            conteudo=None,
            tool_calls=[
                ToolCall(
                    id="1",
                    nome="lotes_de_esquina",
                    argumentos={"loteamento_id": str(loteamento.id), "status": "disponivel", "area_m2_min": 200},
                )
            ],
        ),
        ChatResposta(conteudo="Encontrei 1 lote de esquina disponível com mais de 200m²: L-Esquina.", tool_calls=[]),
    ]
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    service = AgenteService(db_session)
    resposta = await service.perguntar(tenant.id, "quais lotes disponíveis com mais de 200m² são de esquina?")

    assert resposta == "Encontrei 1 lote de esquina disponível com mais de 200m²: L-Esquina."
    assert mock_llm.chat.call_count == 2
    segunda_chamada_mensagens = mock_llm.chat.call_args_list[1].args[0]
    mensagem_tool = next(m for m in segunda_chamada_mensagens if m["role"] == "tool")
    assert "L-Esquina" in mensagem_tool["content"]


@pytest.mark.asyncio
async def test_agente_nao_inventa_quando_tool_nao_encontra_nada(db_session: AsyncSession, monkeypatch):
    tenant = Tenant(name="agente-nao-encontrado", slug="agente-nao-encontrado")
    db_session.add(tenant)
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.chat.side_effect = [
        ChatResposta(
            conteudo=None,
            tool_calls=[ToolCall(id="1", nome="consultar_lote", argumentos={"lote_id": str(uuid4())})],
        ),
        ChatResposta(conteudo="Não encontrei esse lote no sistema.", tool_calls=[]),
    ]
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    service = AgenteService(db_session)
    resposta = await service.perguntar(tenant.id, "me fale sobre o lote XYZ")

    assert resposta == "Não encontrei esse lote no sistema."
    segunda_chamada_mensagens = mock_llm.chat.call_args_list[1].args[0]
    mensagem_tool = next(m for m in segunda_chamada_mensagens if m["role"] == "tool")
    assert '"encontrado":false' in mensagem_tool["content"].replace(" ", "")


@pytest.mark.asyncio
async def test_agente_responde_direto_sem_precisar_de_tool(db_session: AsyncSession, monkeypatch):
    tenant = Tenant(name="agente-sem-tool", slug="agente-sem-tool")
    db_session.add(tenant)
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.chat.return_value = ChatResposta(conteudo="Olá! Como posso ajudar?", tool_calls=[])
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    service = AgenteService(db_session)
    resposta = await service.perguntar(tenant.id, "oi")

    assert resposta == "Olá! Como posso ajudar?"
    mock_llm.chat.assert_called_once()


@pytest.mark.asyncio
async def test_agente_usa_resposta_padrao_quando_modelo_nao_gera_texto(db_session: AsyncSession, monkeypatch):
    tenant = Tenant(name="agente-vazio", slug="agente-vazio")
    db_session.add(tenant)
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.chat.return_value = ChatResposta(conteudo=None, tool_calls=[])
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    service = AgenteService(db_session)
    resposta = await service.perguntar(tenant.id, "???")

    assert resposta == RESPOSTA_PADRAO_SEM_TEXTO


@pytest.mark.asyncio
async def test_endpoint_agente_perguntar(client: AsyncClient, db_session: AsyncSession, monkeypatch):
    """Critério de aceite: `POST /agente/perguntar` funcional, escopado ao tenant autenticado."""
    token, tenant = await _criar_usuario_com_tenant(db_session, "tenant-agente-endpoint")
    loteamento = Loteamento(tenant_id=tenant.id, nome="Loteamento Teste")
    db_session.add(loteamento)
    await db_session.flush()
    lote = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="L1",
        status=LoteStatus.DISPONIVEL, preco=200000,
    )
    db_session.add(lote)
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.chat.side_effect = [
        ChatResposta(
            conteudo=None,
            tool_calls=[
                ToolCall(id="1", nome="buscar_lotes", argumentos={"loteamento_id": str(loteamento.id), "preco_max": 250000})
            ],
        ),
        ChatResposta(conteudo="O lote L1 custa R$200.000 e está disponível.", tool_calls=[]),
    ]
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    response = await client.post(
        "/agente/perguntar",
        json={"pergunta": "quais lotes até R$250 mil estão disponíveis?"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == {"resposta": "O lote L1 custa R$200.000 e está disponível."}
