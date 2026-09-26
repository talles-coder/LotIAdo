"""Add geometry columns to loteamentos/lotes and create feicoes_referencia.

Revision ID: 20260918090000
Revises: 20260917100000
Create Date: 2026-09-18 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from sqlalchemy.dialects import postgresql

revision = '20260918090000'
down_revision = '20260917100000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # spatial_index=False + create_index explícito: controla o nome do índice e
    # evita que o geoalchemy2 crie um índice duplicado.
    op.add_column('loteamentos', sa.Column('geometria', Geometry('POLYGON', srid=4326, spatial_index=False), nullable=True))
    op.add_column('lotes', sa.Column('geometria', Geometry('POLYGON', srid=4326, spatial_index=False), nullable=True))
    op.create_index('ix_loteamentos_geometria', 'loteamentos', ['geometria'], postgresql_using='gist')
    op.create_index('ix_lotes_geometria', 'lotes', ['geometria'], postgresql_using='gist')

    op.create_table(
        'feicoes_referencia',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loteamento_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('nome', sa.String(255), nullable=True),
        sa.Column('geometria', Geometry('GEOMETRY', srid=4326, spatial_index=False), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['loteamento_id'], ['loteamentos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_feicoes_referencia_geometria', 'feicoes_referencia', ['geometria'], postgresql_using='gist')
    op.create_index('ix_feicoes_referencia_loteamento_id', 'feicoes_referencia', ['loteamento_id'])

    # Mesma política de RLS das demais tabelas de domínio (ver 20260915160000).
    op.execute('ALTER TABLE feicoes_referencia ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE feicoes_referencia FORCE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON feicoes_referencia
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.drop_table('feicoes_referencia')
    op.drop_index('ix_lotes_geometria', table_name='lotes')
    op.drop_index('ix_loteamentos_geometria', table_name='loteamentos')
    op.drop_column('lotes', 'geometria')
    op.drop_column('loteamentos', 'geometria')
