# Fase 2 — Multi-tenancy real

Entrega desta fase: RLS ativa e testada em todas as tabelas de domínio, múltiplos tenants de teste isolados de verdade, convite/ativação de usuários, RBAC evoluído além dos 3 papéis iniciais.

## Épico E2.1 — Row-Level Security

### FASE2-EST-01-D1 / FASE2-EST-01-D2 — Estudo: RLS no PostgreSQL com pool assíncrono
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como `ROW LEVEL SECURITY` funciona no Postgres e como configurá-lo corretamente com SQLAlchemy async + pool de conexões, sem vazar contexto de tenant entre requests.
- **Conceitos a entender:** `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`; `CREATE POLICY` usando `current_setting()`; `SET LOCAL` (escopo de transação) vs. `SET` (escopo de sessão/conexão) — por que `SET LOCAL` é o correto quando conexões são reaproveitadas por um pool; risco de "vazamento" de `tenant_id` de uma request para a próxima se usado `SET` em vez de `SET LOCAL`; papel de um usuário de banco "BYPASSRLS" (deve ser evitado para o usuário da aplicação).
- **Material recomendado:** documentação oficial do PostgreSQL sobre Row Security Policies; documentação do SQLAlchemy sobre eventos de conexão (`PoolEvents`/`ConnectionEvents`) para injetar o `SET LOCAL` no início de cada transação.
- **Exercício prático:** em um banco de teste isolado, criar uma tabela com RLS, duas policies para dois "tenants" fictícios, e provar via `psql` que uma sessão só enxerga suas próprias linhas mesmo com um `SELECT *` sem `WHERE`.
- **Critério de conclusão:** consegue explicar por que `SET LOCAL` é obrigatório com pool de conexões, e demonstrar (via exercício) o isolamento funcionando.
- **Paralelizável:** Sim.

### FASE2-IMPL-01 — Ativar RLS em todas as tabelas de domínio
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** nenhuma query da aplicação consegue, mesmo por engano, retornar dados de outro tenant.
- **Descrição:** migration que habilita RLS e cria a policy padrão (`tenant_id = current_setting('app.tenant_id')::uuid`) em todas as tabelas com `tenant_id` (loteamentos, lotes, clientes, corretores, reservas_vendas, audit_log, e as que vierem depois); middleware/dependency do FastAPI que executa `SET LOCAL app.tenant_id = :tenant_id` no início de cada transação, usando o `tenant_id` resolvido do JWT.
- **Pré-requisitos:** FASE2-EST-01-D2.
- **Dependências:** Fase 1 completa (tabelas já existem).
- **Resultado esperado:** toda query passa a respeitar o tenant da sessão automaticamente.
- **Critérios de aceite:** teste de isolamento (ver FASE2-IMPL-02) passa; tentativa manual de query sem `tenant_id` setado retorna zero linhas (fail-closed, não fail-open).
- **Paralelizável:** Não pode ser feito em paralelo com FASE2-IMPL-02 (o teste de isolamento depende desta task existir), mas pode ser feito em paralelo com FASE2-IMPL-03 (convite de usuários).
- **Conhecimentos novos introduzidos:** RLS, `SET LOCAL` em transação, policies Postgres.

### FASE2-IMPL-02 — Testes automatizados de isolamento de tenant
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** garantir, de forma automatizada e contínua, que a Fase 2 realmente isola tenants — não apenas "parece funcionar".
- **Descrição:** criar 2+ tenants de teste com dados próprios (loteamentos, lotes, clientes); para cada endpoint de leitura/escrita, testar que uma sessão autenticada no Tenant A nunca vê/edita dados do Tenant B, inclusive tentando forjar IDs de outro tenant na URL.
- **Pré-requisitos:** FASE2-EST-01-D1.
- **Dependências:** FASE2-IMPL-01.
- **Resultado esperado:** suíte de testes de isolamento cobrindo os principais endpoints de domínio.
- **Critérios de aceite:** suíte passa com RLS ativo e **falha** propositalmente se a policy for removida (validação de que o teste realmente testa algo, não um falso positivo).
- **Paralelizável:** Não (depende de FASE2-IMPL-01).
- **Conhecimentos novos introduzidos:** teste de segurança/isolamento como categoria própria de teste.

## Épico E2.2 — Gestão de usuários e RBAC evoluído

### FASE2-IMPL-03 — Convite, ativação/desativação de usuários
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** um gestor/admin pode convidar novos usuários para o seu tenant e desativá-los depois.
- **Descrição:** endpoint de convite (gera token de convite, associa e-mail + papel pretendido + tenant); endpoint de aceite de convite (cria/ativa o `user` e a `user_tenant_membership`); endpoint de desativação (marca membership como inativa, sem deletar histórico).
- **Pré-requisitos:** nenhum estudo novo além de FASE0/FASE2-EST-01.
- **Dependências:** FASE0-IMPL-05.
- **Resultado esperado:** fluxo completo de convite → aceite → ativação testável via API.
- **Critérios de aceite:** usuário desativado não consegue mais autenticar no tenant; token de convite expira e não é reutilizável após aceito.
- **Paralelizável:** Sim, com FASE2-IMPL-01/02.
- **Conhecimentos novos introduzidos:** fluxo de convite com token de uso único.

### FASE2-IMPL-04 — RBAC evoluído: papéis extensíveis além de admin/gestor/corretor
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** o sistema de permissões não fica travado nos 3 papéis iniciais — novos papéis/permissões podem ser adicionados sem migração de schema.
- **Descrição:** tabela `permissions` (chave, descrição) e `role_permissions` (papel, permissão) em vez de checagem de papel hardcoded no código; dependency do FastAPI que verifica permissão (não papel) nas rotas sensíveis; seed inicial com os papéis admin/gestor/corretor mapeados às permissões equivalentes ao comportamento atual.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE0-IMPL-05, FASE2-IMPL-03.
- **Resultado esperado:** checagem de acesso nas rotas é por permissão, não por nome de papel.
- **Critérios de aceite:** criar um novo papel customizado via seed/migration e associá-lo a um usuário concede exatamente as permissões esperadas, sem alterar código de rota.
- **Paralelizável:** Sim, com FASE2-IMPL-01/02, mas depende de FASE2-IMPL-03 para o fluxo de atribuição de papel no convite.
- **Conhecimentos novos introduzidos:** RBAC baseado em permissões (não em papel fixo), preparando terreno para evolução futura (ABAC) sem implementá-la agora.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE2-EST-01 → FASE2-IMPL-02 (testes de isolamento) → FASE2-IMPL-03 (convite/ativação).
- **Dev 2:** FASE2-EST-01 → FASE2-IMPL-01 (RLS) → FASE2-IMPL-04 (RBAC evoluído).
- **Pontos de sincronização:**
  1. FASE2-IMPL-02 só valida de verdade depois que FASE2-IMPL-01 estiver com a policy ativa — Dev 1 pode escrever a suíte de testes em paralelo, mas rodar contra RLS real só ao final.
  2. FASE2-IMPL-04 depende do formato de `user_tenant_membership.papel` definido em FASE2-IMPL-03 — combinar o nome do campo antes.
