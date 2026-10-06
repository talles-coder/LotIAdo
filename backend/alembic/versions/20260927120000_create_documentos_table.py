"""Create documentos table with RLS, seed documentos:gerenciar permission.

Revision ID: 20260927120000
Revises: 20260918090000
Create Date: 2026-09-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260927120000'
down_revision = '20260918090000'
branch_labels = None
depends_on = None

# Mesmos papéis que já gerenciam loteamentos/lotes (ver 20260915170000) —
# corretor também sobe documentos (contratos, tabelas de preço) no dia a dia.
PERMISSAO = ('documentos:gerenciar', 'Enviar e remover documentos do tenant')
PAPEIS = ('admin', 'gestor', 'corretor')


def upgrade() -> None:
    op.create_table(
        'documentos',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loteamento_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('lote_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('tipo', sa.String(100), nullable=True),
        sa.Column('content_type', sa.String(100), nullable=False),
        sa.Column('tamanho_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_key', sa.String(512), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['loteamento_id'], ['loteamentos.id']),
        sa.ForeignKeyConstraint(['lote_id'], ['lotes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_documentos_tenant_id', 'documentos', ['tenant_id'])
    op.create_index('ix_documentos_loteamento_id', 'documentos', ['loteamento_id'])
    op.create_index('ix_documentos_lote_id', 'documentos', ['lote_id'])

    # Mesma política de RLS das demais tabelas de domínio (ver 20260915160000).
    op.execute('ALTER TABLE documentos ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE documentos FORCE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON documentos
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )

    permissions_table = sa.table(
        'permissions',
        sa.column('id', postgresql.UUID(as_uuid=True)),
        sa.column('key', sa.String),
        sa.column('description', sa.String),
    )
    role_permissions_table = sa.table(
        'role_permissions',
        sa.column('role', sa.String),
        sa.column('permission_id', postgresql.UUID(as_uuid=True)),
    )

    connection = op.get_bind()
    key, description = PERMISSAO
    result = connection.execute(
        permissions_table.insert().values(key=key, description=description).returning(permissions_table.c.id)
    )
    permission_id = result.scalar_one()

    connection.execute(
        role_permissions_table.insert(),
        [{'role': papel, 'permission_id': permission_id} for papel in PAPEIS],
    )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE key = :key)"), {"key": PERMISSAO[0]})
    connection.execute(sa.text("DELETE FROM permissions WHERE key = :key"), {"key": PERMISSAO[0]})
    op.drop_table('documentos')
