"""Testes de integração do módulo loteamentos_lotes (CRUD e transição de status)."""
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.domain.acoes import AcaoAuditoria
from app.audit.domain.models import AuditLog
from app.config import Settings
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def _criar_usuario_com_tenant(db: AsyncSession, tenant_slug: str) -> str:
    """Cria um usuário com membership em um tenant e retorna o token JWT."""
    token, _user, _tenant = await _criar_usuario_com_tenant_completo(db, tenant_slug)
    return token


async def _criar_usuario_com_tenant_completo(
    db: AsyncSession, tenant_slug: str
) -> tuple[str, User, Tenant]:
    """Cria um usuário com membership em um tenant e retorna (token, user, tenant)."""
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

    token = create_access_token(user.id, tenant.id, Settings())
    return token, user, tenant


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _criar_loteamento(client: AsyncClient, token: str, nome: str = "Loteamento Teste") -> str:
    response = await client.post(
        "/loteamentos", json={"nome": nome}, headers=_auth_headers(token)
    )
    return response.json()["id"]


async def _criar_lote(client: AsyncClient, token: str, loteamento_id: str, identificacao: str = "Lote 1") -> dict:
    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes",
        json={"identificacao": identificacao},
        headers=_auth_headers(token),
    )
    return response.json()


@pytest.mark.asyncio
async def test_criar_e_obter_loteamento(client: AsyncClient, db_session: AsyncSession):
    """Criar um loteamento retorna 201 e ele pode ser recuperado depois."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-criar")

    criado = await client.post(
        "/loteamentos",
        json={"nome": "Residencial Sol Nascente", "descricao": "Fase 1"},
        headers=_auth_headers(token),
    )
    assert criado.status_code == 201
    loteamento_id = criado.json()["id"]

    obtido = await client.get(f"/loteamentos/{loteamento_id}", headers=_auth_headers(token))
    assert obtido.status_code == 200
    assert obtido.json()["nome"] == "Residencial Sol Nascente"


@pytest.mark.asyncio
async def test_listar_loteamentos_isola_por_tenant(client: AsyncClient, db_session: AsyncSession):
    """Um tenant não vê loteamentos cadastrados por outro tenant."""
    token_a = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-a")
    token_b = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-b")

    await _criar_loteamento(client, token_a)

    response = await client.get("/loteamentos", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_atualizar_loteamento(client: AsyncClient, db_session: AsyncSession):
    """Atualizar um loteamento altera somente os campos informados."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-atualizar")
    loteamento_id = await _criar_loteamento(client, token, nome="Nome Antigo")

    response = await client.patch(
        f"/loteamentos/{loteamento_id}", json={"nome": "Nome Novo"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["nome"] == "Nome Novo"


@pytest.mark.asyncio
async def test_remover_loteamento_e_remocao_logica(client: AsyncClient, db_session: AsyncSession):
    """Remover um loteamento é lógico: some da listagem mas não é hard-delete."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-remover")
    loteamento_id = await _criar_loteamento(client, token)

    delete_response = await client.delete(f"/loteamentos/{loteamento_id}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/loteamentos/{loteamento_id}", headers=_auth_headers(token))
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_obter_loteamento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Buscar um loteamento com id inexistente retorna 404."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-loteamento-404")

    response = await client.get(
        "/loteamentos/00000000-0000-0000-0000-000000000000", headers=_auth_headers(token)
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_criar_lote_em_loteamento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    """Criar um lote em um loteamento inexistente (ou de outro tenant) retorna 404."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-404")

    response = await client.post(
        "/loteamentos/00000000-0000-0000-0000-000000000000/lotes",
        json={"identificacao": "Lote 1"},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_criar_lote_com_status_inicial_disponivel(client: AsyncClient, db_session: AsyncSession):
    """Um lote recém-criado começa com status DISPONIVEL."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-criar")
    loteamento_id = await _criar_loteamento(client, token)

    lote = await _criar_lote(client, token, loteamento_id)

    assert lote["status"] == "disponivel"
    assert lote["loteamento_id"] == loteamento_id


@pytest.mark.asyncio
async def test_listar_lotes_isola_por_tenant(client: AsyncClient, db_session: AsyncSession):
    """Um tenant não vê lotes cadastrados por outro tenant."""
    token_a = await _criar_usuario_com_tenant(db_session, "tenant-lote-a")
    token_b = await _criar_usuario_com_tenant(db_session, "tenant-lote-b")

    loteamento_a = await _criar_loteamento(client, token_a)
    await _criar_lote(client, token_a, loteamento_a)

    loteamento_b = await _criar_loteamento(client, token_b)
    response = await client.get(f"/loteamentos/{loteamento_b}/lotes", headers=_auth_headers(token_b))

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_atualizar_lote(client: AsyncClient, db_session: AsyncSession):
    """Atualizar um lote altera somente os campos informados, sem tocar o status."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-atualizar")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    response = await client.patch(
        f"/lotes/{lote['id']}", json={"preco": "150000.00"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["preco"] == "150000.00"
    assert body["status"] == "disponivel"


@pytest.mark.asyncio
async def test_transicao_de_status_valida(client: AsyncClient, db_session: AsyncSession):
    """Transição permitida (DISPONIVEL -> RESERVADO) é aplicada e retorna 200."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-transicao-valida")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    response = await client.patch(
        f"/lotes/{lote['id']}/status", json={"status": "reservado"}, headers=_auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reservado"


@pytest.mark.asyncio
async def test_transicao_de_status_invalida_retorna_409(client: AsyncClient, db_session: AsyncSession):
    """Transição proibida (DISPONIVEL -> VENDIDO) retorna 409 com mensagem clara."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-transicao-invalida")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    response = await client.patch(
        f"/lotes/{lote['id']}/status", json={"status": "vendido"}, headers=_auth_headers(token)
    )

    assert response.status_code == 409
    assert "disponivel" in response.json()["detail"]
    assert "vendido" in response.json()["detail"]


@pytest.mark.asyncio
async def test_remover_lote_e_remocao_logica(client: AsyncClient, db_session: AsyncSession):
    """Remover um lote é lógico: some da listagem mas não é hard-delete."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-lote-remover")
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    delete_response = await client.delete(f"/lotes/{lote['id']}", headers=_auth_headers(token))
    assert delete_response.status_code == 204

    get_response = await client.get(f"/lotes/{lote['id']}", headers=_auth_headers(token))
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_loteamentos_sem_token_retorna_401(client: AsyncClient):
    """Acesso a /loteamentos sem token retorna 401."""
    response = await client.get("/loteamentos")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_preview_importacao_csv_retorna_cabecalhos(client: AsyncClient, db_session: AsyncSession):
    """O preview de um CSV retorna os cabeçalhos encontrados, na ordem em que aparecem no arquivo."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-import-preview")
    loteamento_id = await _criar_loteamento(client, token)

    csv_content = "Preço,Identificação,Quadra\n150000,L1,Q1\n"
    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar/preview",
        files={"arquivo": ("lotes.csv", csv_content, "text/csv")},
        headers=_auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["colunas"] == ["Preço", "Identificação", "Quadra"]


@pytest.mark.asyncio
async def test_confirmar_importacao_csv_cria_lotes_com_colunas_em_ordem_arbitraria(
    client: AsyncClient, db_session: AsyncSession
):
    """Um CSV com colunas em ordem/nome arbitrário é importado corretamente após o mapeamento."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-import-confirma")
    loteamento_id = await _criar_loteamento(client, token)

    csv_content = "preco,id_lote,setor,tamanho\n150000.00,L1,Q1,300.5\n200000.00,L2,Q2,250\n"
    mapeamento = {
        "identificacao": "id_lote",
        "quadra": "setor",
        "area_m2": "tamanho",
        "preco": "preco",
    }

    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar",
        files={"arquivo": ("lotes.csv", csv_content, "text/csv")},
        data={"mapeamento": json.dumps(mapeamento)},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["total_linhas"] == 2
    assert body["importados"] == 2
    assert body["erros"] == []

    listagem = await client.get(f"/loteamentos/{loteamento_id}/lotes", headers=_auth_headers(token))
    lotes = {lote["identificacao"]: lote for lote in listagem.json()}
    assert lotes["L1"]["quadra"] == "Q1"
    assert lotes["L1"]["area_m2"] == "300.50"
    assert lotes["L1"]["preco"] == "150000.00"
    assert lotes["L2"]["area_m2"] == "250.00"


@pytest.mark.asyncio
async def test_confirmar_importacao_csv_reporta_linhas_invalidas_sem_abortar_o_restante(
    client: AsyncClient, db_session: AsyncSession
):
    """Linhas inválidas (identificação vazia, preço não numérico) são reportadas, sem abortar o import."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-import-erros")
    loteamento_id = await _criar_loteamento(client, token)

    csv_content = (
        "id_lote,preco\n"
        "L1,150000.00\n"
        ",200000.00\n"
        "L3,nao-e-numero\n"
        "L4,180000.00\n"
    )
    mapeamento = {"identificacao": "id_lote", "preco": "preco"}

    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar",
        files={"arquivo": ("lotes.csv", csv_content, "text/csv")},
        data={"mapeamento": json.dumps(mapeamento)},
        headers=_auth_headers(token),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["total_linhas"] == 4
    assert body["importados"] == 2
    linhas_com_erro = {erro["linha"] for erro in body["erros"]}
    assert linhas_com_erro == {3, 4}

    listagem = await client.get(f"/loteamentos/{loteamento_id}/lotes", headers=_auth_headers(token))
    identificacoes = {lote["identificacao"] for lote in listagem.json()}
    assert identificacoes == {"L1", "L4"}


@pytest.mark.asyncio
async def test_confirmar_importacao_csv_com_mapeamento_sem_identificacao_retorna_400(
    client: AsyncClient, db_session: AsyncSession
):
    """Mapeamento sem a coluna obrigatória 'identificacao' é rejeitado antes de importar qualquer linha."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-import-mapeamento-invalido")
    loteamento_id = await _criar_loteamento(client, token)

    csv_content = "id_lote,preco\nL1,150000.00\n"
    response = await client.post(
        f"/loteamentos/{loteamento_id}/lotes/importar",
        files={"arquivo": ("lotes.csv", csv_content, "text/csv")},
        data={"mapeamento": json.dumps({"preco": "preco"})},
        headers=_auth_headers(token),
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_confirmar_importacao_csv_em_loteamento_inexistente_retorna_404(
    client: AsyncClient, db_session: AsyncSession
):
    """Importar um CSV em um loteamento inexistente (ou de outro tenant) retorna 404."""
    token = await _criar_usuario_com_tenant(db_session, "tenant-import-404")

    csv_content = "id_lote\nL1\n"
    response = await client.post(
        "/loteamentos/00000000-0000-0000-0000-000000000000/lotes/importar",
        files={"arquivo": ("lotes.csv", csv_content, "text/csv")},
        data={"mapeamento": json.dumps({"identificacao": "id_lote"})},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_transicao_de_status_gera_uma_entrada_de_auditoria(
    client: AsyncClient, db_session: AsyncSession
):
    """Uma transição de status via API gera exatamente uma entrada em audit_log, com o payload correto.

    Critério de aceite da SCRUM-54 (FASE1-IMPL-04) para o lado de
    loteamentos_lotes: a auditoria é automática (`Lote` é decorado com
    `@rastrear_auditoria`, ver app/loteamentos_lotes/domain/models.py) —
    nenhuma chamada explícita é feita pelo service ou pela rota.
    """
    token, user, tenant = await _criar_usuario_com_tenant_completo(
        db_session, "tenant-lote-auditoria"
    )
    loteamento_id = await _criar_loteamento(client, token)
    lote = await _criar_lote(client, token, loteamento_id)

    response = await client.patch(
        f"/lotes/{lote['id']}/status", json={"status": "reservado"}, headers=_auth_headers(token)
    )
    assert response.status_code == 200

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.entidade_id == lote["id"])
    )
    entradas = result.scalars().all()

    assert len(entradas) == 1
    entrada = entradas[0]
    assert entrada.acao == AcaoAuditoria.TRANSICAO_STATUS
    assert entrada.entidade == "lote"
    assert entrada.tenant_id == tenant.id
    assert entrada.usuario_id == user.id
    assert entrada.payload_antes == {"status": "disponivel"}
    assert entrada.payload_depois == {"status": "reservado"}
