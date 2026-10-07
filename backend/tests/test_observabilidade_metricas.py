"""Testes das métricas agregadas de IA (SCRUM-110)."""
import json
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.observabilidade.application.metricas_service import MetricasIAService
from app.tenancy.domain.models import Tenant


def _escrever_eventos(caminho: Path, eventos: list[dict]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        for evento in eventos:
            arquivo.write(json.dumps(evento) + "\n")


def test_metricas_com_arquivo_inexistente_retorna_tudo_zerado(tmp_path):
    metricas = MetricasIAService(caminho_log=tmp_path / "nao-existe.jsonl").obter_metricas()
    assert metricas.total_chamadas == 0
    assert metricas.chamadas_com_erro == 0
    assert metricas.taxa_erro == 0.0
    assert metricas.latencia_media_ms is None
    assert metricas.por_origem == []


def test_metricas_agrega_por_origem_com_cenario_conhecido(tmp_path):
    """3 chamadas RAG (1 com erro) + 2 chamadas AGENTE (0 erro) → totais e por-origem batem."""
    caminho = tmp_path / "app-ia.jsonl"
    _escrever_eventos(
        caminho,
        [
            {"origem": "rag", "metodo": "embed", "latencia_ms": 100.0, "sucesso": True},
            {"origem": "rag", "metodo": "embed", "latencia_ms": 200.0, "sucesso": True},
            {"origem": "rag", "metodo": "generate", "latencia_ms": 300.0, "sucesso": False, "erro": "timeout"},
            {"origem": "agente", "metodo": "chat", "latencia_ms": 50.0, "sucesso": True},
            {"origem": "agente", "metodo": "chat", "latencia_ms": 150.0, "sucesso": True},
        ],
    )

    metricas = MetricasIAService(caminho_log=caminho).obter_metricas()

    assert metricas.total_chamadas == 5
    assert metricas.chamadas_com_erro == 1
    assert metricas.taxa_erro == pytest.approx(0.2)
    assert metricas.latencia_media_ms == pytest.approx(160.0)  # (100+200+300+50+150)/5

    por_origem = {item.origem: item for item in metricas.por_origem}
    assert por_origem["rag"].total_chamadas == 3
    assert por_origem["rag"].chamadas_com_erro == 1
    assert por_origem["rag"].latencia_media_ms == pytest.approx(200.0)  # (100+200+300)/3
    assert por_origem["agente"].total_chamadas == 2
    assert por_origem["agente"].chamadas_com_erro == 0
    assert por_origem["agente"].latencia_media_ms == pytest.approx(100.0)  # (50+150)/2


def test_metricas_ignora_linha_json_invalida(tmp_path):
    caminho = tmp_path / "app-ia.jsonl"
    caminho.write_text(
        '{"origem": "rag", "metodo": "embed", "latencia_ms": 10.0, "sucesso": true}\n'
        "isso não é json\n"
        '{"origem": "rag", "metodo": "embed", "latencia_ms": 20.0, "sucesso": true}\n',
        encoding="utf-8",
    )

    metricas = MetricasIAService(caminho_log=caminho).obter_metricas()

    assert metricas.total_chamadas == 2


async def _criar_usuario_com_papel(db: AsyncSession, tenant_slug: str, role: str) -> str:
    tenant = Tenant(name=tenant_slug, slug=tenant_slug)
    db.add(tenant)
    await db.flush()

    user = User(email=f"{tenant_slug}@test.com", hashed_password=hash_password("senha123"), full_name="Test User")
    db.add(user)
    await db.flush()

    db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role=role))
    await db.commit()

    return create_access_token(user.id, tenant.id, Settings())


@pytest.mark.asyncio
async def test_endpoint_metricas_exige_permissao_observabilidade_visualizar(client: AsyncClient, db_session: AsyncSession):
    token_corretor = await _criar_usuario_com_papel(db_session, "tenant-metricas-sem-permissao", "corretor")

    response = await client.get("/observabilidade/metricas", headers={"Authorization": f"Bearer {token_corretor}"})

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_endpoint_metricas_retorna_agregado_para_admin(client: AsyncClient, db_session: AsyncSession, monkeypatch, tmp_path):
    caminho = tmp_path / "app-ia.jsonl"
    _escrever_eventos(
        caminho,
        [
            {"origem": "rag", "metodo": "embed", "latencia_ms": 100.0, "sucesso": True},
            {"origem": "rag", "metodo": "embed", "latencia_ms": 300.0, "sucesso": False, "erro": "timeout"},
        ],
    )
    monkeypatch.setattr("app.observabilidade.application.metricas_service.CAMINHO_LOG_IA", caminho)
    token_admin = await _criar_usuario_com_papel(db_session, "tenant-metricas-admin", "admin")

    response = await client.get("/observabilidade/metricas", headers={"Authorization": f"Bearer {token_admin}"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_chamadas"] == 2
    assert body["chamadas_com_erro"] == 1
    assert body["taxa_erro"] == pytest.approx(0.5)
    assert body["por_origem"] == [{"origem": "rag", "total_chamadas": 2, "chamadas_com_erro": 1, "latencia_media_ms": 200.0}]
