"""Create audit_log table.

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
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('acao', sa.String(100), nullable=False),
        sa.Column('entidade', sa.String(100), nullable=False),
        sa.Column('entidade_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payload_antes', sa.JSON, nullable=True),
        sa.Column('payload_depois', sa.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('audit_log')
