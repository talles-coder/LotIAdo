"""Add is_active to user_tenant_membership.

Revision ID: 20260917090000
Revises: 20260916090000
Create Date: 2026-09-17 09:00:00.000000

Suporte a desativação de usuário (SCRUM-59 / FASE2-IMPL-03): a membership é
marcada inativa em vez de removida, preservando o histórico (auditoria,
reservas/vendas já associadas ao corretor, etc).
"""
from alembic import op
import sqlalchemy as sa

revision = '20260917090000'
down_revision = '20260916090000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'user_tenant_membership',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column('user_tenant_membership', 'is_active')
