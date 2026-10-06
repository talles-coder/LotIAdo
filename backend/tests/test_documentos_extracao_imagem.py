"""Testes da sugestão de extração de imagem de planta (OCR + contornos, FASE8-IMPL-02/SCRUM-100)."""
import contextlib
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import cv2
import numpy as np
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.documentos.domain.models import Documento
from app.documentos.infrastructure.extracao_imagem import extrair_contornos, extrair_sugestoes
from app.identity.application.security import create_access_token, hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


def _png_com_retangulo() -> bytes:
    """Imagem sintética (fundo branco + retângulo preto) — contorno detectável sem depender do Tesseract."""
    imagem = np.full((200, 200, 3), 255, dtype=np.uint8)
    cv2.rectangle(imagem, (40, 40), (160, 160), (0, 0, 0), thickness=3)
    ok, buffer = cv2.imencode(".png", imagem)
    assert ok
    return buffer.tobytes()


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


async def _criar_documento(db: AsyncSession, tenant: Tenant, content_type: str = "image/png") -> Documento:
    documento = Documento(
        tenant_id=tenant.id,
        nome="planta.png",
        content_type=content_type,
        tamanho_bytes=100,
        storage_key="documentos/teste/planta.png",
    )
    db.add(documento)
    await db.commit()
    await db.refresh(documento)
    return documento


# --- Pipeline puro (OCR + contornos), sem I/O de banco/fila ---


def test_extrair_contornos_encontra_o_retangulo_desenhado():
    """`extrair_contornos` é OpenCV puro: valida sem depender do binário do Tesseract."""
    contornos = extrair_contornos(_png_com_retangulo())

    assert len(contornos) >= 1
    maior = contornos[0]
    assert len(maior["pontos"]) >= 4
    assert maior["area"] > 0


def test_extrair_sugestoes_nunca_gera_geometria_geografica():
    """O resultado é sempre em coordenadas de pixel — nunca lat/lng (critério de aceite SCRUM-100)."""
    with patch("app.documentos.infrastructure.extracao_imagem._ocr_dados") as mock_ocr:
        mock_ocr.return_value = {"text": ["L-01"], "conf": ["92"], "left": [10], "top": [10], "width": [30], "height": [12]}
        resultado = extrair_sugestoes(_png_com_retangulo())

    assert resultado["identificacoes"] == [{"texto": "L-01", "confianca": 92.0, "bbox": [10, 10, 30, 12]}]
    assert len(resultado["contornos"]) >= 1
    for contorno in resultado["contornos"]:
        for ponto in contorno["pontos"]:
            assert isinstance(ponto[0], int) and isinstance(ponto[1], int)


def test_extrair_identificacoes_descarta_texto_de_baixa_confianca():
    with patch("app.documentos.infrastructure.extracao_imagem._ocr_dados") as mock_ocr:
        mock_ocr.return_value = {
            "text": ["L-01", "ruido"],
            "conf": ["92", "10"],
            "left": [10, 50],
            "top": [10, 50],
            "width": [30, 20],
            "height": [12, 10],
        }
        resultado = extrair_sugestoes(_png_com_retangulo())

    assert [i["texto"] for i in resultado["identificacoes"]] == ["L-01"]


# --- Job RQ (async, mesmo padrão de test_ai_rag_ingestao.py) ---


@pytest.mark.asyncio
async def test_processar_extracao_imagem_preenche_resultado_e_marca_concluido(db_session: AsyncSession, monkeypatch):
    """`extrair_sugestoes` (o boundary do OCR/CV, ver testes acima) é mockado aqui — o binário do
    Tesseract nem sempre está instalado na máquina que roda a suíte (só é obrigatório no worker,
    `infra/worker/Dockerfile`); o que este teste garante é a orquestração do job, não o CV em si."""
    from app.documentos.application.extracao_imagem_service import _processar_extracao_imagem_async

    _, tenant = await _criar_usuario_com_tenant(db_session, "tenant-extracao-imagem")
    documento = await _criar_documento(db_session, tenant)

    monkeypatch.setattr(
        "app.documentos.application.extracao_imagem_service.MinioStorage.baixar",
        AsyncMock(return_value=_png_com_retangulo()),
    )
    monkeypatch.setattr(
        "app.documentos.application.extracao_imagem_service.extrair_sugestoes",
        lambda conteudo: {"identificacoes": [{"texto": "L-01", "confianca": 92.0, "bbox": [1, 2, 3, 4]}], "contornos": [{"pontos": [[0, 0], [10, 0], [10, 10]], "area": 100.0}]},
    )
    monkeypatch.setattr(
        "app.documentos.application.extracao_imagem_service.async_session",
        lambda: contextlib.nullcontext(db_session),
    )

    await _processar_extracao_imagem_async(str(documento.id), str(tenant.id))

    await db_session.refresh(documento)
    assert documento.status_extracao_imagem == "concluido"
    assert len(documento.resultado_extracao_imagem["contornos"]) >= 1


@pytest.mark.asyncio
async def test_processar_extracao_imagem_marca_falhou_quando_erro(db_session: AsyncSession, monkeypatch):
    from app.documentos.application.extracao_imagem_service import _processar_extracao_imagem_async

    _, tenant = await _criar_usuario_com_tenant(db_session, "tenant-extracao-imagem-falha")
    documento = await _criar_documento(db_session, tenant)

    monkeypatch.setattr(
        "app.documentos.application.extracao_imagem_service.MinioStorage.baixar",
        AsyncMock(side_effect=RuntimeError("MinIO indisponível")),
    )
    monkeypatch.setattr(
        "app.documentos.application.extracao_imagem_service.async_session",
        lambda: contextlib.nullcontext(db_session),
    )

    with pytest.raises(RuntimeError):
        await _processar_extracao_imagem_async(str(documento.id), str(tenant.id))

    await db_session.refresh(documento)
    assert documento.status_extracao_imagem == "falhou"


@pytest.mark.asyncio
async def test_processar_extracao_imagem_inexistente_nao_levanta_erro(db_session: AsyncSession):
    from app.documentos.application.extracao_imagem_service import _processar_extracao_imagem_async

    _, tenant = await _criar_usuario_com_tenant(db_session, "tenant-extracao-imagem-inexistente")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.documentos.application.extracao_imagem_service.async_session",
            lambda: contextlib.nullcontext(db_session),
        )
        await _processar_extracao_imagem_async(str(uuid4()), str(tenant.id))


# --- Rotas HTTP ---


@pytest.mark.asyncio
async def test_sugerir_extracao_imagem_enfileira_job_e_fica_pendente(client: AsyncClient, db_session: AsyncSession):
    """Pedir a sugestão enfileira o job (SCRUM-100) sem bloquear a resposta, status inicial `pendente`."""
    import redis
    from rq import Queue

    from app.ai_rag.infrastructure.queue import NOME_FILA

    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-extracao-imagem-rota")
    fila = Queue(NOME_FILA, connection=redis.from_url(Settings().redis_url))
    fila.empty()

    upload = await client.post(
        "/documentos",
        files={"arquivo": ("planta.png", _png_com_retangulo(), "image/png")},
        data={},
        headers=_auth_headers(token),
    )
    assert upload.status_code == 201
    documento_id = upload.json()["id"]
    fila.empty()  # o upload já enfileira o job de indexação (FASE7-IMPL-01); zera pra isolar o teste

    resposta = await client.post(f"/documentos/{documento_id}/sugerir-extracao-imagem", headers=_auth_headers(token))

    assert resposta.status_code == 202
    assert resposta.json()["status_extracao_imagem"] == "pendente"
    assert fila.count == 1


@pytest.mark.asyncio
async def test_sugerir_extracao_imagem_rejeita_documento_nao_imagem(client: AsyncClient, db_session: AsyncSession):
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-extracao-imagem-nao-imagem")

    upload = await client.post(
        "/documentos",
        files={"arquivo": ("memorial.pdf", b"%PDF-1.4 conteudo de teste", "application/pdf")},
        data={},
        headers=_auth_headers(token),
    )
    documento_id = upload.json()["id"]

    resposta = await client.post(f"/documentos/{documento_id}/sugerir-extracao-imagem", headers=_auth_headers(token))

    assert resposta.status_code == 400


@pytest.mark.asyncio
async def test_sugerir_extracao_imagem_documento_inexistente_retorna_404(client: AsyncClient, db_session: AsyncSession):
    token, _ = await _criar_usuario_com_tenant(db_session, "tenant-extracao-imagem-404")

    resposta = await client.post(
        "/documentos/00000000-0000-0000-0000-000000000000/sugerir-extracao-imagem",
        headers=_auth_headers(token),
    )

    assert resposta.status_code == 404


@pytest.mark.asyncio
async def test_obter_documento_retorna_resultado_apos_processamento(client: AsyncClient, db_session: AsyncSession):
    """A tela de calibração faz poll de GET /documentos/{id} até `status_extracao_imagem` concluir."""
    from app.documentos.application.extracao_imagem_service import _processar_extracao_imagem_async

    token, tenant = await _criar_usuario_com_tenant(db_session, "tenant-extracao-imagem-poll")

    upload = await client.post(
        "/documentos",
        files={"arquivo": ("planta.png", _png_com_retangulo(), "image/png")},
        data={},
        headers=_auth_headers(token),
    )
    documento_id = upload.json()["id"]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.documentos.application.extracao_imagem_service.MinioStorage.baixar",
            AsyncMock(return_value=_png_com_retangulo()),
        )
        mp.setattr(
            "app.documentos.application.extracao_imagem_service.extrair_sugestoes",
            lambda conteudo: {"identificacoes": [], "contornos": [{"pontos": [[0, 0], [10, 0], [10, 10]], "area": 100.0}]},
        )
        mp.setattr(
            "app.documentos.application.extracao_imagem_service.async_session",
            lambda: contextlib.nullcontext(db_session),
        )
        await _processar_extracao_imagem_async(documento_id, str(tenant.id))

    resposta = await client.get(f"/documentos/{documento_id}", headers=_auth_headers(token))

    assert resposta.status_code == 200
    body = resposta.json()
    assert body["status_extracao_imagem"] == "concluido"
    assert len(body["resultado_extracao_imagem"]["contornos"]) >= 1
