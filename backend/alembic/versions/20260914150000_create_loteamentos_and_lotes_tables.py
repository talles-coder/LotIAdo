"""Create loteamentos and lotes tables.

Revision ID: 20260914150000
Revises: 20260914120000
Create Date: 2026-09-14 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260914150000'
down_revision = '20260914120000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'loteamentos',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('nome', sa.String(255), nullable=False),
        sa.Column('descricao', sa.String(1000), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'lotes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('loteamento_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('identificacao', sa.String(50), nullable=False),
        sa.Column('quadra', sa.String(50), nullable=True),
        sa.Column('area_m2', sa.Numeric(10, 2), nullable=True),
        sa.Column('preco', sa.Numeric(12, 2), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='disponivel'),
        sa.Column('caracteristicas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('corretor_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cliente_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['loteamento_id'], ['loteamentos.id']),
        sa.ForeignKeyConstraint(['corretor_id'], ['corretores.id']),
        sa.ForeignKeyConstraint(['cliente_id'], ['clientes.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('lotes')
    op.drop_table('loteamentos')
