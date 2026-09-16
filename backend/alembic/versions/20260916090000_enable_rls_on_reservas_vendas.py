"""Enable Row-Level Security on reservas_vendas.

Revision ID: 20260916090000
Revises: 20260916085000
Create Date: 2026-09-16 09:00:00.000000

`reservas_vendas` (SCRUM-53) foi criada depois de `20260915160000` (RLS,
FASE2-IMPL-01) e ficou de fora daquela migration — fechando o gap
encontrado ao escrever a suíte de isolamento por tenant da SCRUM-58
(FASE2-IMPL-02). Encadeada depois do merge `20260916085000` (não direto
em `20260915103000`) porque precisa que a cadeia de `permissions` já
tenha rodado tanto quanto a de `reservas_vendas`.
"""
from alembic import op

revision = '20260916090000'
down_revision = '20260916085000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('ALTER TABLE reservas_vendas ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE reservas_vendas FORCE ROW LEVEL SECURITY')
    op.execute(
        """
        CREATE POLICY tenant_isolation ON reservas_vendas
        USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
        WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    op.execute('DROP POLICY IF EXISTS tenant_isolation ON reservas_vendas')
    op.execute('ALTER TABLE reservas_vendas NO FORCE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE reservas_vendas DISABLE ROW LEVEL SECURITY')
