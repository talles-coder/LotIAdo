"""Testes unitários das tools de consulta do agente (FASE9-IMPL-01/SCRUM-103).

Cada tool é chamada diretamente (sem HTTP, sem grafo do agente), com
parâmetros de exemplo, validando o formato do schema Pydantic de saída.
"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, box
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_agents.application.tools import (
    buscar_documentos,
    buscar_lotes,
    consultar_clientes,
    consultar_condicoes_comerciais,
    consultar_corretores,
    consultar_disponibilidade,
    consultar_lote,
    consultar_vendas,
    distancia_entre_lotes,
    lotes_de_esquina,
    lotes_dentro_de,
    lotes_proximos_de,
)
from app.ai_agents.domain.schemas import (
    BuscarDocumentosInput,
    BuscarLotesInput,
    ConsultarClientesInput,
    ConsultarCondicoesComerciaisInput,
    ConsultarCorretoresInput,
    ConsultarDisponibilidadeInput,
    ConsultarLoteInput,
    ConsultarVendasInput,
    DistanciaEntreLotesInput,
    LotesDentroDeInput,
    LotesDeEsquinaInput,
    LotesProximosDeInput,
)
from app.ai_rag.domain.models import DocumentChunk
from app.audit.infrastructure.context import contexto_auditoria
from app.clientes.domain.models import Cliente
from app.config import Settings
from app.corretores.domain.models import Corretor
from app.documentos.domain.models import Documento
from app.geo.domain.models import FeicaoReferencia, TipoFeicao
from app.identity.application.security import hash_password
from app.identity.domain.models import User
from app.loteamentos_lotes.domain.models import Lote, Loteamento
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.tenancy.domain.models import Tenant
from app.vendas_reservas.domain.models import ReservaVenda, StatusReservaVenda, TipoReservaVenda


async def _criar_tenant(db: AsyncSession, slug: str) -> Tenant:
    tenant = Tenant(name=slug, slug=slug)
    db.add(tenant)
    await db.commit()
    return tenant


async def _criar_usuario(db: AsyncSession, slug: str) -> User:
    user = User(email=f"{slug}@test.com", hashed_password=hash_password("senha123"), full_name="Test User")
    db.add(user)
    await db.commit()
    return user


async def _criar_loteamento(db: AsyncSession, tenant: Tenant, nome: str = "Loteamento Teste") -> Loteamento:
    loteamento = Loteamento(tenant_id=tenant.id, nome=nome)
    db.add(loteamento)
    await db.commit()
    return loteamento


@pytest.mark.asyncio
async def test_consultar_lote(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-consultar-lote")
    loteamento = await _criar_loteamento(db_session, tenant)
    lote = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="L1", area_m2=250, preco=90000
    )
    db_session.add(lote)
    await db_session.commit()

    encontrado = await consultar_lote(db_session, tenant.id, ConsultarLoteInput(lote_id=lote.id))
    inexistente = await consultar_lote(db_session, tenant.id, ConsultarLoteInput(lote_id=uuid4()))

    assert encontrado.encontrado is True
    assert encontrado.lote.identificacao == "L1"
    assert encontrado.lote.preco == 90000
    assert inexistente.encontrado is False
    assert inexistente.lote is None


@pytest.mark.asyncio
async def test_buscar_lotes_filtra_por_status_area_e_preco(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-buscar-lotes")
    loteamento = await _criar_loteamento(db_session, tenant)
    db_session.add_all(
        [
            Lote(
                tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="Barato",
                status=LoteStatus.DISPONIVEL, area_m2=150, preco=50000,
            ),
            Lote(
                tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="Caro",
                status=LoteStatus.DISPONIVEL, area_m2=400, preco=300000,
            ),
            Lote(
                tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="Reservado",
                status=LoteStatus.RESERVADO, area_m2=200, preco=80000,
            ),
        ]
    )
    await db_session.commit()

    resultado = await buscar_lotes(
        db_session,
        tenant.id,
        BuscarLotesInput(loteamento_id=loteamento.id, status=LoteStatus.DISPONIVEL, preco_max=100000),
    )

    assert resultado.total == 1
    assert resultado.lotes[0].identificacao == "Barato"


@pytest.mark.asyncio
async def test_consultar_disponibilidade(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-disponibilidade")
    loteamento = await _criar_loteamento(db_session, tenant)
    lote = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="L1", status=LoteStatus.RESERVADO
    )
    db_session.add(lote)
    await db_session.commit()

    resultado = await consultar_disponibilidade(db_session, tenant.id, ConsultarDisponibilidadeInput(lote_id=lote.id))

    assert resultado.encontrado is True
    assert resultado.status == LoteStatus.RESERVADO
    assert resultado.disponivel is False


@pytest.mark.asyncio
async def test_lotes_de_esquina(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-lotes-esquina")
    loteamento = await _criar_loteamento(db_session, tenant)
    esquina = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="Esquina",
        geometria=from_shape(box(0, 0, 0.001, 0.001), srid=4326),
    )
    db_session.add(esquina)
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

    resultado = await lotes_de_esquina(db_session, tenant.id, LotesDeEsquinaInput(loteamento_id=loteamento.id))

    assert resultado.encontrado is True
    assert resultado.total == 1
    assert resultado.lotes[0].identificacao == "Esquina"


@pytest.mark.asyncio
async def test_lotes_proximos_de(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-lotes-proximos")
    loteamento = await _criar_loteamento(db_session, tenant)
    lote = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="Perto",
        geometria=from_shape(box(0.0001, 0.0001, 0.0011, 0.0011), srid=4326),
    )
    area_verde = FeicaoReferencia(
        tenant_id=tenant.id, loteamento_id=loteamento.id, tipo=TipoFeicao.AREA_VERDE, nome="Praça",
        geometria=from_shape(box(-0.001, -0.001, 0, 0), srid=4326),
    )
    db_session.add_all([lote, area_verde])
    await db_session.commit()

    proximo = await lotes_proximos_de(
        db_session, tenant.id, LotesProximosDeInput(feicao_id=area_verde.id, raio_m=100)
    )
    feicao_inexistente = await lotes_proximos_de(
        db_session, tenant.id, LotesProximosDeInput(feicao_id=uuid4(), raio_m=100)
    )

    assert proximo.encontrado is True
    assert proximo.total == 1
    assert feicao_inexistente.encontrado is False


@pytest.mark.asyncio
async def test_lotes_dentro_de(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-lotes-dentro")
    loteamento = await _criar_loteamento(db_session, tenant)
    lote = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="Dentro",
        geometria=from_shape(box(0, 0, 0.001, 0.001), srid=4326),
    )
    db_session.add(lote)
    await db_session.commit()
    area = {"type": "Polygon", "coordinates": [list(box(-0.001, -0.001, 0.002, 0.002).exterior.coords)]}

    dentro = await lotes_dentro_de(db_session, tenant.id, LotesDentroDeInput(area_geojson=area))
    invalido = await lotes_dentro_de(
        db_session, tenant.id, LotesDentroDeInput(area_geojson={"type": "Point", "coordinates": [0, 0]})
    )

    assert dentro.encontrado is True
    assert dentro.total == 1
    assert invalido.encontrado is False


@pytest.mark.asyncio
async def test_distancia_entre_lotes(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-distancia")
    loteamento = await _criar_loteamento(db_session, tenant)
    lote_a = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="A",
        geometria=from_shape(box(0, 0, 0.001, 0.001), srid=4326),
    )
    lote_b = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="B",
        geometria=from_shape(box(0.001, 0, 0.002, 0.001), srid=4326),
    )
    db_session.add_all([lote_a, lote_b])
    await db_session.commit()

    resultado = await distancia_entre_lotes(
        db_session, tenant.id, DistanciaEntreLotesInput(lote_a_id=lote_a.id, lote_b_id=lote_b.id)
    )

    assert resultado.encontrado is True
    assert resultado.distancia_m == pytest.approx(0, abs=0.01)


@pytest.mark.asyncio
async def test_consultar_clientes(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-clientes")
    cliente = Cliente(tenant_id=tenant.id, nome="Maria", documento="123", contato="maria@test.com")
    db_session.add(cliente)
    await db_session.commit()

    por_id = await consultar_clientes(db_session, tenant.id, ConsultarClientesInput(cliente_id=cliente.id))
    todos = await consultar_clientes(db_session, tenant.id, ConsultarClientesInput())

    assert por_id.encontrado is True
    assert por_id.clientes[0].nome == "Maria"
    assert todos.total == 1


@pytest.mark.asyncio
async def test_consultar_corretores(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-corretores")
    corretor = Corretor(tenant_id=tenant.id, nome="João", contato="joao@test.com")
    db_session.add(corretor)
    await db_session.commit()

    por_id = await consultar_corretores(db_session, tenant.id, ConsultarCorretoresInput(corretor_id=corretor.id))
    todos = await consultar_corretores(db_session, tenant.id, ConsultarCorretoresInput())

    assert por_id.encontrado is True
    assert por_id.corretores[0].nome == "João"
    assert todos.total == 1


@pytest.mark.asyncio
async def test_consultar_vendas(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-vendas")
    usuario = await _criar_usuario(db_session, "tools-vendas")
    loteamento = await _criar_loteamento(db_session, tenant)
    lote = Lote(tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="L1", status=LoteStatus.RESERVADO)
    cliente = Cliente(tenant_id=tenant.id, nome="Maria", documento="123", contato="maria@test.com")
    db_session.add_all([lote, cliente])
    await db_session.flush()
    with contexto_auditoria(usuario_id=usuario.id, tenant_id=tenant.id):
        reserva = ReservaVenda(
            tenant_id=tenant.id, lote_id=lote.id, cliente_id=cliente.id,
            tipo=TipoReservaVenda.RESERVA, status=StatusReservaVenda.RESERVADO,
        )
        db_session.add(reserva)
        await db_session.commit()

    por_id = await consultar_vendas(db_session, tenant.id, ConsultarVendasInput(reserva_id=reserva.id))
    por_lote = await consultar_vendas(db_session, tenant.id, ConsultarVendasInput(lote_id=lote.id))
    sem_parametros = await consultar_vendas(db_session, tenant.id, ConsultarVendasInput())

    assert por_id.encontrado is True
    assert por_id.reserva.status == StatusReservaVenda.RESERVADO
    assert por_lote.encontrado is True
    assert sem_parametros.encontrado is False


@pytest.mark.asyncio
async def test_buscar_documentos(db_session: AsyncSession, monkeypatch):
    tenant = await _criar_tenant(db_session, "tools-documentos")
    dim = Settings().embedding_dimensions
    documento = Documento(
        tenant_id=tenant.id, nome="memorial.txt", content_type="text/plain", tamanho_bytes=10,
        storage_key=f"documentos/{tenant.id}/memorial.txt", status_indexacao="concluido",
    )
    db_session.add(documento)
    await db_session.commit()
    chunk = DocumentChunk(
        documento_id=documento.id, tenant_id=tenant.id, ordem=0, texto="condições de pagamento",
        embedding=[1.0] * dim,
    )
    db_session.add(chunk)
    await db_session.commit()

    mock_llm = AsyncMock()
    mock_llm.embed.return_value = [1.0] * dim
    monkeypatch.setattr(ai_rag, "llm_provider", mock_llm)

    resultado = await buscar_documentos(db_session, tenant.id, BuscarDocumentosInput(pergunta="como pagar?"))

    assert resultado.encontrado is True
    assert resultado.resultados[0].texto == "condições de pagamento"


@pytest.mark.asyncio
async def test_consultar_condicoes_comerciais(db_session: AsyncSession):
    tenant = await _criar_tenant(db_session, "tools-condicoes")
    loteamento = await _criar_loteamento(db_session, tenant)
    lote = Lote(
        tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="L1", preco=120000, area_m2=300,
        caracteristicas={"aceita_financiamento": True},
    )
    db_session.add(lote)
    await db_session.commit()

    resultado = await consultar_condicoes_comerciais(
        db_session, tenant.id, ConsultarCondicoesComerciaisInput(lote_id=lote.id)
    )

    assert resultado.encontrado is True
    assert resultado.preco == 120000
    assert resultado.caracteristicas == {"aceita_financiamento": True}
