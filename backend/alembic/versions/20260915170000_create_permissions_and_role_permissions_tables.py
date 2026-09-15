"""Create permissions and role_permissions tables, seed admin/gestor/corretor.

Revision ID: 20260915170000
Revises: 20260915160000
Create Date: 2026-09-15 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260915170000'
down_revision = '20260915160000'
branch_labels = None
depends_on = None

# Permissões equivalentes ao comportamento atual: qualquer membro autenticado
# do tenant pode gerenciar (criar/atualizar/remover) estes recursos. O papel
# deixa de ser checado diretamente nas rotas — a checagem passa a ser por
# permissão, resolvida via `role_permissions` — o que permite criar papéis
# customizados (ex: "financeiro") sem alterar código de rota (ver
# FASE2-IMPL-04 em docs/backlog/fase-2-multi-tenancy.md).
PERMISSOES = (
    ('clientes:gerenciar', 'Criar, atualizar e remover clientes do tenant'),
    ('corretores:gerenciar', 'Criar, atualizar e remover corretores do tenant'),
    ('loteamentos_lotes:gerenciar', 'Criar, atualizar e remover loteamentos e lotes do tenant'),
)

PAPEIS_INICIAIS = ('admin', 'gestor', 'corretor')


def upgrade() -> None:
    op.create_table(
        'permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )

    op.create_table(
        'role_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('permission_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role', 'permission_id', name='uq_role_permissions'),
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
    permission_ids = {}
    for key, description in PERMISSOES:
        result = connection.execute(
            permissions_table.insert().values(key=key, description=description).returning(permissions_table.c.id)
        )
        permission_ids[key] = result.scalar_one()

    connection.execute(
        role_permissions_table.insert(),
        [
            {'role': papel, 'permission_id': permission_id}
            for papel in PAPEIS_INICIAIS
            for permission_id in permission_ids.values()
        ],
    )


def downgrade() -> None:
    op.drop_table('role_permissions')
    op.drop_table('permissions')
