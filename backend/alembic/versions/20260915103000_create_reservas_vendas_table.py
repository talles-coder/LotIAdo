"""Create reservas_vendas table.

Revision ID: 20260915103000
Revises: 20260915170000
Create Date: 2026-09-15 10:30:00.000000

Rebaseada para depois de `20260915170000` (permissions) porque, no commit
original, esta migration e `20260915160000` (enable RLS) divergiam do mesmo
pai (`20260915090000`), gerando dois heads de migration simultâneos — o que
faria `alembic upgrade head` falhar com "Multiple head revisions are
present". `reservas_vendas` não é tocada por nenhuma das duas, então
reordenar é seguro.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260915103000'
down_revision = '20260915170000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'reservas_vendas',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lote_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('corretor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tipo', sa.String(20), nullable=False, server_default='reserva'),
        sa.Column('status', sa.String(20), nullable=False, server_default='reservado'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['lote_id'], ['lotes.id']),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id']),
        sa.ForeignKeyConstraint(['corretor_id'], ['corretores.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('reservas_vendas')
