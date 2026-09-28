"""Seed observabilidade:visualizar permission for admin/gestor.

Revision ID: 20260928120000
Revises: 20260927140000
Create Date: 2026-09-28 12:00:00.000000

Mesmo critério de `usuarios:gerenciar` (20260917100000): só `admin`/`gestor`
veem o dashboard de métricas de IA (SCRUM-110/FASE10-IMPL-02) — não `corretor`.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260928120000'
down_revision = '20260927140000'
branch_labels = None
depends_on = None

PERMISSAO = ('observabilidade:visualizar', 'Ver o dashboard de métricas de chamadas de IA (latência, volume, erros)')
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
