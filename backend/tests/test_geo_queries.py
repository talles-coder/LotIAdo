"""Testes de integração das consultas espaciais (GeoQueryService + endpoints /geo).

Layout de teste (graus perto do equador; 0.001° ≈ 111 m), calculável à mão:

    y=0.001   +---L1---+---L2---+        +---L3---+     [AV]
    y=0       ==== Rua A (y=0, x de -0.001 a 0.004) =====
              x=0      0.001    0.002   0.003    0.004  0.0042–0.005

Rua B: vertical em x=0 (toca a aresta esquerda de L1).
Rua C: vertical em x=0.002 (toca a aresta direita de L2).
AV: área verde à direita de L3.
"""
import pytest
from geoalchemy2.shape import from_shape
from httpx import AsyncClient
from shapely.geometry import LineString, Polygon, box
from sqlalchemy.ext.asyncio import AsyncSession

from app.geo.domain.models import FeicaoReferencia, TipoFeicao
from app.loteamentos_lotes.domain.models import Lote, Loteamento
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from tests.test_loteamentos_lotes import _auth_headers, _criar_usuario_com_tenant_completo

# 0.002° de longitude no equador (WGS84) = 0.002 * 111319.49 m
DISTANCIA_L1_L3_M = 222.64


def _lote(tenant_id, loteamento_id, ident, x0, x1, status, area_m2):
    return Lote(
        tenant_id=tenant_id,
        loteamento_id=loteamento_id,
        identificacao=ident,
        status=status,
        area_m2=area_m2,
        geometria=from_shape(box(x0, 0, x1, 0.001), srid=4326),
    )


def _feicao(tenant_id, loteamento_id, tipo, geom, nome):
    return FeicaoReferencia(
        tenant_id=tenant_id,
        loteamento_id=loteamento_id,
        tipo=tipo,
        nome=nome,
        geometria=from_shape(geom, srid=4326),
    )


async def _cenario(db: AsyncSession, slug: str):
    token, _user, tenant = await _criar_usuario_com_tenant_completo(db, slug)
    loteamento = Loteamento(tenant_id=tenant.id, nome="Residencial Geo")
    db.add(loteamento)
    await db.flush()

    lotes = {
        "L1": _lote(tenant.id, loteamento.id, "L1", 0, 0.001, LoteStatus.RESERVADO, 150),
        "L2": _lote(tenant.id, loteamento.id, "L2", 0.001, 0.002, LoteStatus.DISPONIVEL, 250),
        "L3": _lote(tenant.id, loteamento.id, "L3", 0.003, 0.004, LoteStatus.DISPONIVEL, 300),
    }
    db.add_all(lotes.values())
    db.add_all(
        [
            _feicao(tenant.id, loteamento.id, TipoFeicao.RUA, LineString([(-0.001, 0), (0.004, 0)]), "Rua A"),
            _feicao(tenant.id, loteamento.id, TipoFeicao.RUA, LineString([(0, -0.001), (0, 0.002)]), "Rua B"),
            _feicao(tenant.id, loteamento.id, TipoFeicao.RUA, LineString([(0.002, -0.001), (0.002, 0.002)]), "Rua C"),
        ]
    )
    area_verde = _feicao(
        tenant.id, loteamento.id, TipoFeicao.AREA_VERDE, box(0.0042, 0, 0.005, 0.001), "Praça"
    )
    db.add(area_verde)
    await db.commit()
    return token, tenant, loteamento, lotes, area_verde


def _identificacoes(response) -> set[str]:
    assert response.status_code == 200, response.text
    return {lote["identificacao"] for lote in response.json()}


@pytest.mark.asyncio
async def test_distancia_entre_lotes(client: AsyncClient, db_session: AsyncSession):
    token, _t, _l, lotes, _av = await _cenario(db_session, "geo-distancia")

    distante = await client.get(
        "/geo/distancia",
        params={"lote_a": str(lotes["L1"].id), "lote_b": str(lotes["L3"].id)},
        headers=_auth_headers(token),
    )
    vizinhos = await client.get(
        "/geo/distancia",
        params={"lote_a": str(lotes["L1"].id), "lote_b": str(lotes["L2"].id)},
        headers=_auth_headers(token),
    )

    assert distante.status_code == 200
    assert distante.json()["distancia_m"] == pytest.approx(DISTANCIA_L1_L3_M, abs=0.5)
    assert vizinhos.json()["distancia_m"] == pytest.approx(0, abs=0.01)


@pytest.mark.asyncio
async def test_distancia_lote_inexistente_ou_sem_geometria(client: AsyncClient, db_session: AsyncSession):
    token, tenant, loteamento, lotes, _av = await _cenario(db_session, "geo-distancia-erro")
    sem_geometria = Lote(tenant_id=tenant.id, loteamento_id=loteamento.id, identificacao="SG")
    db_session.add(sem_geometria)
    await db_session.commit()

    inexistente = await client.get(
        "/geo/distancia",
        params={"lote_a": str(lotes["L1"].id), "lote_b": "00000000-0000-0000-0000-000000000000"},
        headers=_auth_headers(token),
    )
    sem_geo = await client.get(
        "/geo/distancia",
        params={"lote_a": str(lotes["L1"].id), "lote_b": str(sem_geometria.id)},
        headers=_auth_headers(token),
    )

    assert inexistente.status_code == 404
    assert sem_geo.status_code == 422


@pytest.mark.asyncio
async def test_lotes_de_esquina_com_filtros_de_negocio(client: AsyncClient, db_session: AsyncSession):
    token, _t, loteamento, _lotes, _av = await _cenario(db_session, "geo-esquina")
    url = f"/geo/loteamentos/{loteamento.id}/lotes-de-esquina"

    todos = await client.get(url, headers=_auth_headers(token))
    disponiveis = await client.get(url, params={"status": "disponivel"}, headers=_auth_headers(token))
    grandes = await client.get(url, params={"area_m2_min": 200}, headers=_auth_headers(token))
    grandes_reservados = await client.get(
        url, params={"status": "reservado", "area_m2_min": 200}, headers=_auth_headers(token)
    )

    # L1 toca Rua A + Rua B; L2 toca Rua A + Rua C; L3 toca só Rua A.
    assert _identificacoes(todos) == {"L1", "L2"}
    assert _identificacoes(disponiveis) == {"L2"}
    assert _identificacoes(grandes) == {"L2"}
    assert _identificacoes(grandes_reservados) == set()


@pytest.mark.asyncio
async def test_lotes_proximos_de_feicao(client: AsyncClient, db_session: AsyncSession):
    token, _t, _l, _lotes, area_verde = await _cenario(db_session, "geo-proximos")
    url = f"/geo/feicoes/{area_verde.id}/lotes-proximos"

    # L3 está a ~22 m da praça, L2 a ~245 m, L1 a ~467 m.
    perto = await client.get(url, params={"raio_m": 50}, headers=_auth_headers(token))
    medio = await client.get(url, params={"raio_m": 300}, headers=_auth_headers(token))
    medio_reservado = await client.get(
        url, params={"raio_m": 300, "status": "disponivel", "area_m2_min": 280}, headers=_auth_headers(token)
    )

    assert _identificacoes(perto) == {"L3"}
    assert _identificacoes(medio) == {"L2", "L3"}
    assert _identificacoes(medio_reservado) == {"L3"}


@pytest.mark.asyncio
async def test_lotes_proximos_feicao_inexistente(client: AsyncClient, db_session: AsyncSession):
    token, *_ = await _cenario(db_session, "geo-proximos-404")

    response = await client.get(
        "/geo/feicoes/00000000-0000-0000-0000-000000000000/lotes-proximos",
        params={"raio_m": 50},
        headers=_auth_headers(token),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_lotes_dentro_de_area(client: AsyncClient, db_session: AsyncSession):
    token, _t, loteamento, _lotes, _av = await _cenario(db_session, "geo-dentro")
    url = "/geo/lotes/dentro-de"

    def area(x1):
        return {"type": "Polygon", "coordinates": [list(box(-0.0005, -0.0005, x1, 0.0015).exterior.coords)]}

    cobre_l1_l2 = await client.post(url, json={"area_geojson": area(0.0025)}, headers=_auth_headers(token))
    corta_l2 = await client.post(url, json={"area_geojson": area(0.0015)}, headers=_auth_headers(token))
    so_disponiveis = await client.post(
        url,
        json={"area_geojson": area(0.0025), "status": "disponivel", "loteamento_id": str(loteamento.id)},
        headers=_auth_headers(token),
    )

    assert _identificacoes(cobre_l1_l2) == {"L1", "L2"}
    assert _identificacoes(corta_l2) == {"L1"}  # L2 só parcialmente dentro: fora
    assert _identificacoes(so_disponiveis) == {"L2"}


@pytest.mark.asyncio
async def test_lotes_dentro_de_area_invalida(client: AsyncClient, db_session: AsyncSession):
    token, *_ = await _cenario(db_session, "geo-dentro-invalido")
    gravata = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])  # auto-interseção

    ponto = await client.post(
        "/geo/lotes/dentro-de",
        json={"area_geojson": {"type": "Point", "coordinates": [0, 0]}},
        headers=_auth_headers(token),
    )
    lixo = await client.post(
        "/geo/lotes/dentro-de", json={"area_geojson": {"foo": "bar"}}, headers=_auth_headers(token)
    )
    invalido = await client.post(
        "/geo/lotes/dentro-de",
        json={"area_geojson": {"type": "Polygon", "coordinates": [list(gravata.exterior.coords)]}},
        headers=_auth_headers(token),
    )

    assert ponto.status_code == lixo.status_code == invalido.status_code == 422


@pytest.mark.asyncio
async def test_consultas_nao_vazam_entre_tenants(client: AsyncClient, db_session: AsyncSession):
    _token_a, _t, loteamento_a, lotes_a, area_verde_a = await _cenario(db_session, "geo-tenant-a")
    token_b, *_ = await _cenario(db_session, "geo-tenant-b")

    esquina = await client.get(
        f"/geo/loteamentos/{loteamento_a.id}/lotes-de-esquina", headers=_auth_headers(token_b)
    )
    proximos = await client.get(
        f"/geo/feicoes/{area_verde_a.id}/lotes-proximos", params={"raio_m": 500}, headers=_auth_headers(token_b)
    )
    distancia = await client.get(
        "/geo/distancia",
        params={"lote_a": str(lotes_a["L1"].id), "lote_b": str(lotes_a["L2"].id)},
        headers=_auth_headers(token_b),
    )

    assert esquina.json() == []
    assert proximos.status_code == 404
    assert distancia.status_code == 404
