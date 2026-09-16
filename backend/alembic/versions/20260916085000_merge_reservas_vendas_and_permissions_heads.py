"""Merge reservas_vendas and permissions/RLS migration heads.

Revision ID: 20260916085000
Revises: 20260915103000, 20260915170000
Create Date: 2026-09-16 08:50:00.000000

`20260915103000` (create reservas_vendas) e `20260915170000` (permissions,
no topo da cadeia de RLS) divergiam do mesmo pai (`20260915090000`) por
terem sido escritas em paralelo, gerando dois heads simultâneos —
`alembic upgrade head` falhava com "Multiple head revisions are present".

Um merge migration (em vez de reescrever o `down_revision` de uma das duas
migrations já publicadas) é a forma correta de resolver: quem já rodou
qualquer um dos dois branches mantém uma cadeia de histórico válida — só
reescrever o `down_revision` de uma migration já aplicada faz o Alembic
pular migrations que nunca rodaram de fato num banco carimbado no branch
antigo (foi exatamente isso que aconteceu ao tentar a abordagem de
reordenar, na SCRUM-59: `alembic upgrade head` reportava sucesso sem
nunca ter criado `permissions`/`role_permissions`).
"""
revision = '20260916085000'
down_revision = ('20260915103000', '20260915170000')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
