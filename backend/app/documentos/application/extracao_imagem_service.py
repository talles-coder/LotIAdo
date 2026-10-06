"""Pipeline de sugestão de extração de planta (OCR + contornos), via job RQ (FASE8-IMPL-02/SCRUM-100).

Mesmo padrão de `app/ai_rag/application/ingestao_service.py`: job síncrono do RQ chamando
`asyncio.run()` sobre a lógica assíncrona, `tenant_id` viaja como argumento do job (RLS da tabela
`documentos` exige `app.tenant_id` setado antes do SELECT). Nunca escreve geometria/identificação
definitiva — só preenche `resultado_extracao_imagem` com sugestões em pixel, revisadas manualmente
na tela de calibração (FASE5-IMPL-03) antes de qualquer persistência real.
"""
from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.database import async_session
from app.documentos.domain.models import Documento
from app.documentos.infrastructure.extracao_imagem import extrair_sugestoes
from app.documentos.infrastructure.storage import MinioStorage


async def _set_tenant(db: AsyncSession, tenant_id: UUID) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})


async def _buscar_documento(db: AsyncSession, tenant_id: UUID, documento_id: UUID) -> Documento | None:
    await _set_tenant(db, tenant_id)
    result = await db.execute(
        select(Documento).where(Documento.id == documento_id, Documento.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def _marcar_status(db: AsyncSession, documento: Documento, status: str, resultado: dict | None = None) -> None:
    documento.status_extracao_imagem = status
    if resultado is not None:
        documento.resultado_extracao_imagem = resultado
    await db.commit()


async def _processar_extracao_imagem_async(documento_id: str, tenant_id: str) -> None:
    settings = Settings()
    documento_uuid = UUID(documento_id)
    tenant_uuid = UUID(tenant_id)

    async with async_session() as db:
        documento = await _buscar_documento(db, tenant_uuid, documento_uuid)
        if documento is None:
            return

        await _marcar_status(db, documento, "processando")

        try:
            conteudo = await MinioStorage(settings).baixar(documento.storage_key)
            resultado = extrair_sugestoes(conteudo)
            await _marcar_status(db, documento, "concluido", resultado)
        except Exception:
            await _marcar_status(db, documento, "falhou")
            raise


def processar_extracao_imagem(documento_id: str, tenant_id: str) -> None:
    """Job RQ: OCR + detecção de contornos sobre a imagem de uma planta (FASE8-IMPL-02)."""
    import asyncio

    asyncio.run(_processar_extracao_imagem_async(documento_id, tenant_id))
