"""Create document_chunks table (pgvector) and add status_indexacao to documentos.

Revision ID: 20260927130000
Revises: 20260927120000
Create Date: 2026-09-27 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision = '20260927130000'
down_revision = '20260927120000'
branch_labels = None
depends_on = None

# D6 (docs/backlog/fase-7-documentos-rag.md): nomic-embed-text, 768 dimensões
# — precisa bater com `Settings.embedding_dimensions` (app/config.py).
DIMENSOES_EMBEDDING = 768


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    op.add_column(
        'documentos',
        sa.Column('status_indexacao', sa.String(20), nullable=False, server_default='pendente'),
    )

    op.create_table(
        'document_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('documento_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loteamento_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lote_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ordem', sa.Integer(), nullable=False),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(DIMENSOES_EMBEDDING), nullable=False),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id']),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['loteamento_id'], ['loteamentos.id']),
        sa.ForeignKeyConstraint(['lote_id'], ['lotes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_chunks_documento_id', 'document_chunks', ['documento_id'])
    op.create_index('ix_document_chunks_tenant_id', 'document_chunks', ['tenant_id'])

    # Mesma política de RLS das demais tabelas de domínio (ver 20260915160000):
    # filtro explícito de tenant_id nas queries de busca vetorial (FASE7-IMPL-03)
    # é defesa em profundidade além desta policy, não substituto dela.
    op.execute('ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE document_chunks FORCE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON document_chunks
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.drop_table('document_chunks')
    op.drop_column('documentos', 'status_indexacao')
