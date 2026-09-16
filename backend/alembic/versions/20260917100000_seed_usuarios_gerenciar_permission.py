"""Seed usuarios:gerenciar permission for admin/gestor.

Revision ID: 20260917100000
Revises: 20260917093000
Create Date: 2026-09-17 10:00:00.000000

Só `admin`/`gestor` recebem esta permissão (não `corretor`) — SCRUM-59
(FASE2-IMPL-03) descreve o fluxo de convite/desativação como algo que "um
gestor/admin" faz, não um corretor.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260917100000'
down_revision = '20260917093000'
branch_labels = None
depends_on = None

PERMISSAO = ('usuarios:gerenciar', 'Convidar, aceitar convite e desativar usuários do tenant')
PAPEIS = ('admin', 'gestor')


def upgrade() -> None:
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
