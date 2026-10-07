"""Cria o tenant/dados determinísticos usados pelo golden-set de avaliação (FASE10-IMPL-03/SCRUM-113).

Idempotente: se o tenant `golden-set` já existir, não faz nada (mesmo
comportamento de `scripts/seed_user.py`). IDs de todas as entidades são
determinísticos (`eval/ids.py`), então `eval/golden_set.yaml` e
`scripts/avaliar_golden_set.py` nunca precisam de um UUID gravado em disco.

Uso:
    cd backend
    python -m scripts.seed_golden_set

Requer Ollama local rodando (gera embeddings reais dos chunks do documento —
mesmo pipeline de produção, sem atalho).
"""
import asyncio

from geoalchemy2.shape import from_shape
from shapely.geometry import LineString, box
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

import app.ai_rag as ai_rag
from app.ai_rag.domain.models import DocumentChunk
from app.ai_rag.infrastructure.chunking import dividir_em_chunks
from app.database import async_session
from app.documentos.domain.models import Documento
from app.geo.domain.models import FeicaoReferencia, TipoFeicao
from app.identity.application.security import hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.loteamentos_lotes.domain.models import Lote, Loteamento
from app.loteamentos_lotes.domain.state_machine import LoteStatus
from app.tenancy.domain.models import Tenant
from eval.ids import (
    AREA_VERDE_ID,
    DOCUMENTO_ID,
    LOTE_IDS,
    LOTEAMENTO_ID,
    RUA_A_ID,
    RUA_B_ID,
    TENANT_ID,
    TENANT_NOME,
    TENANT_SLUG,
    USUARIO_EMAIL,
    USUARIO_ID,
    USUARIO_SENHA,
)

MEMORIAL_TEXTO = (
    "O Loteamento Golden Eval fica no município de Avaliação, GO, com área total de 50.000 m² "
    "distribuída em 42 lotes.\n\n"
    "O prazo de entrega da infraestrutura (rede elétrica, água tratada e pavimentação asfáltica) "
    "é de 12 meses a partir da assinatura do contrato.\n\n"
    "A área verde central conta com praça e playground, a menos de 100 metros dos lotes da Quadra 1."
)


async def _set_tenant(db: AsyncSession, tenant_id) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :tenant_id, true)"), {"tenant_id": str(tenant_id)})


async def seed_golden_set() -> None:
    async with async_session() as db:
        existente = await db.execute(select(Tenant).where(Tenant.id == TENANT_ID))
        if existente.scalar_one_or_none() is not None:
            print(f"Tenant '{TENANT_SLUG}' já existia ({TENANT_ID}) — nada a fazer.")
            return

        db.add(Tenant(id=TENANT_ID, name=TENANT_NOME, slug=TENANT_SLUG))
        db.add(User(id=USUARIO_ID, email=USUARIO_EMAIL, hashed_password=hash_password(USUARIO_SENHA), full_name="Golden Eval"))
        await db.flush()
        db.add(UserTenantMembership(user_id=USUARIO_ID, tenant_id=TENANT_ID, role="admin"))
        await db.commit()

        await _set_tenant(db, TENANT_ID)

        db.add(Loteamento(id=LOTEAMENTO_ID, tenant_id=TENANT_ID, nome="Loteamento Golden Eval"))

        # Esquina: GE-01 toca duas ruas perpendiculares (mesmo padrão de
        # test_lotes_de_esquina em tests/test_ai_agents_tools.py).
        db.add_all(
            [
                FeicaoReferencia(
                    id=RUA_A_ID, tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID, tipo=TipoFeicao.RUA, nome="Rua A",
                    geometria=from_shape(LineString([(-0.001, 0), (0.002, 0)]), srid=4326),
                ),
                FeicaoReferencia(
                    id=RUA_B_ID, tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID, tipo=TipoFeicao.RUA, nome="Rua B",
                    geometria=from_shape(LineString([(0, -0.001), (0, 0.002)]), srid=4326),
                ),
                # Área verde: GE-03 fica a ~11 m da borda (dentro do raio de 100 m usado no golden-set).
                FeicaoReferencia(
                    id=AREA_VERDE_ID, tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID, tipo=TipoFeicao.AREA_VERDE,
                    nome="Praça Central", geometria=from_shape(box(0.019, 0.019, 0.020, 0.020), srid=4326),
                ),
            ]
        )

        db.add_all(
            [
                Lote(
                    id=LOTE_IDS["GE-01"], tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID, identificacao="GE-01",
                    area_m2=250, preco=180000, status=LoteStatus.DISPONIVEL,
                    geometria=from_shape(box(0, 0, 0.001, 0.001), srid=4326),
                ),
                Lote(
                    id=LOTE_IDS["GE-02"], tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID, identificacao="GE-02",
                    area_m2=120, preco=95000, status=LoteStatus.DISPONIVEL,
                    geometria=from_shape(box(0.01, 0.01, 0.0105, 0.0105), srid=4326),
                ),
                Lote(
                    id=LOTE_IDS["GE-03"], tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID, identificacao="GE-03",
                    area_m2=180, preco=230000, status=LoteStatus.DISPONIVEL,
                    geometria=from_shape(box(0.0201, 0.0201, 0.0211, 0.0211), srid=4326),
                ),
                Lote(
                    id=LOTE_IDS["GE-04"], tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID, identificacao="GE-04",
                    area_m2=300, preco=500000, status=LoteStatus.VENDIDO,
                    geometria=from_shape(box(0.05, 0.05, 0.0505, 0.0505), srid=4326),
                ),
            ]
        )

        documento = Documento(
            id=DOCUMENTO_ID, tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID,
            nome="Memorial Descritivo Golden Eval.txt", tipo="memorial", content_type="text/plain",
            tamanho_bytes=len(MEMORIAL_TEXTO.encode("utf-8")), storage_key=f"eval/{TENANT_ID}/memorial.txt",
            status_indexacao="concluido",
        )
        db.add(documento)

        for ordem, chunk_texto in enumerate(dividir_em_chunks(MEMORIAL_TEXTO)):
            embedding = await ai_rag.llm_provider.embed(chunk_texto)
            db.add(
                DocumentChunk(
                    documento_id=DOCUMENTO_ID, tenant_id=TENANT_ID, loteamento_id=LOTEAMENTO_ID,
                    ordem=ordem, texto=chunk_texto, embedding=embedding,
                )
            )

        await db.commit()
        print(f"Tenant '{TENANT_SLUG}' criado ({TENANT_ID}) — login {USUARIO_EMAIL}/{USUARIO_SENHA}.")
        print("Loteamento Golden Eval com 4 lotes (GE-01..GE-04), 2 ruas, 1 área verde e 1 documento indexado.")


def main() -> None:
    asyncio.run(seed_golden_set())


if __name__ == "__main__":
    main()
