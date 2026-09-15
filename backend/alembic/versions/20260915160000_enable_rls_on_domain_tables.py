"""Enable Row-Level Security on tenant-scoped domain tables.

Revision ID: 20260915160000
Revises: 20260915090000
Create Date: 2026-09-15 16:00:00.000000

"""
from alembic import op

revision = '20260915160000'
down_revision = '20260915090000'
branch_labels = None
depends_on = None

# `user_tenant_membership` (e `users`, `tenants`) fica de fora de propósito:
# é a própria tabela usada para *resolver* o tenant no login/`/me`, antes de
# haver um `app.tenant_id` de sessão para comparar — habilitar RLS nela
# criaria uma dependência circular (ver FASE2-IMPL-01 em
# docs/backlog/fase-2-multi-tenancy.md).
TABELAS_COM_RLS = (
    'clientes',
    'corretores',
    'loteamentos',
    'lotes',
    'audit_log',
)


def upgrade() -> None:
    for tabela in TABELAS_COM_RLS:
        op.execute(f'ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY')
        # FORCE é necessário porque o dono da tabela (papel usado pelas
        # migrations) senão ficaria isento da policy por padrão; a aplicação
        # roda com o papel `lotiado_app`, que não é dono nem superusuário
        # (ver infra/postgres/init/03-create-app-role.sql), então FORCE só
        # reforça a defesa em profundidade.
        op.execute(f'ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY')
        # `current_setting(..., true)` com o segundo argumento `true` (missing_ok)
        # retorna NULL em vez de lançar erro quando `app.tenant_id` não foi
        # setado na sessão/transação — e `tenant_id = NULL` nunca é
        # verdadeiro, então a policy falha fechada (zero linhas), não aberta.
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {tabela}
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
            """
        )


def downgrade() -> None:
    for tabela in reversed(TABELAS_COM_RLS):
        op.execute(f'DROP POLICY IF EXISTS tenant_isolation ON {tabela}')
        op.execute(f'ALTER TABLE {tabela} NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY')
