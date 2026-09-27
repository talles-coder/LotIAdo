"""Add status_extracao_imagem/resultado_extracao_imagem to documentos (FASE8-IMPL-02/SCRUM-100).

Revision ID: 20260927140000
Revises: 20260927130000
Create Date: 2026-09-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '20260927140000'
down_revision = '20260927130000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # `status_extracao_imagem` fica NULL até o usuário pedir a sugestão de extração (documento não
    # é necessariamente uma planta) — diferente de `status_indexacao`, que roda pra todo documento.
    op.add_column('documentos', sa.Column('status_extracao_imagem', sa.String(20), nullable=True))
    op.add_column('documentos', sa.Column('resultado_extracao_imagem', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('documentos', 'resultado_extracao_imagem')
    op.drop_column('documentos', 'status_extracao_imagem')
