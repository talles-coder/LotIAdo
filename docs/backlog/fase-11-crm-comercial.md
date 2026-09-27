# Fase 11 — CRM Comercial & Funil de Vendas

Entrega desta fase: leads entram num funil com estágios explícitos, são distribuídos automaticamente entre corretores, negociações passam por um workflow simples de aprovação de crédito, e a trilha de auditoria por lote (já existente desde a Fase 1) fica visível na UI. Nenhuma tecnologia nova é introduzida — tudo reaproveita domínio (Fase 1), RBAC (Fase 2) e o módulo de auditoria já construído; por isso não há tasks de estudo nesta fase.

## Épico E11.1 — Funil de leads

### FASE11-IMPL-01 — Modelo de Lead e estágios do funil
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** todo interessado em um lote é registrado como `Lead`, com um estágio explícito do funil (`novo` → `qualificando` → `em_negociacao` → `convertido`/`perdido`), antes de virar uma reserva/venda formal.
- **Descrição:** entidade `Lead` com `tenant_id`, dados de contato, lote(s) de interesse, corretor responsável, estágio atual e motivo quando `perdido`; transição de estágio decorada com `@rastrear_auditoria` (mesmo padrão da Fase 1, decisão registrada em `03-decisoes-tecnicas.md`); conversão de um lead em reserva/venda vincula o registro existente ao lead de origem (rastreabilidade de onde veio a venda).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE1-IMPL-01/03 (models e auditoria), FASE2 (RBAC para permissão de quem move estágio).
- **Resultado esperado:** CRUD de lead com transição de estágio validada (não pula estágio, não sai de `convertido`/`perdido`).
- **Critérios de aceite:** tentativa de transição inválida (ex.: `novo` → `convertido` direto) é rejeitada; toda transição gera entrada de auditoria.
- **Paralelizável:** Sim, com FASE11-IMPL-04.
- **Conhecimentos novos introduzidos:** nenhum.

### FASE11-IMPL-02 — Distribuição automática de leads entre corretores
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** um lead novo é atribuído automaticamente a um corretor ativo, sem intervenção manual do gestor.
- **Descrição:** estratégia round-robin simples entre corretores ativos do tenant (ordenado por quem recebeu lead há mais tempo); reatribuição manual pelo gestor continua possível e sobrescreve a automática.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE11-IMPL-01.
- **Resultado esperado:** todo lead criado sem corretor explícito recebe um responsável automaticamente.
- **Critérios de aceite:** teste com 3 corretores ativos e 6 leads confirma distribuição 2/2/2 na ordem de criação; corretor inativo nunca recebe lead novo.
- **Paralelizável:** Não pode ser finalizada sem FASE11-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E11.2 — Aprovação de crédito

### FASE11-IMPL-03 — Workflow de aprovação de crédito
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** uma negociação em estágio avançado do funil passa por um status explícito de análise de crédito antes de virar venda.
- **Descrição:** status manual (`pendente`/`aprovado`/`reprovado`) na negociação, com anexo de documento comprobatório reaproveitando o storage já abstraído (MinIO/S3, Fase 5) — **sem integração com bureau de crédito externo**, é decisão humana registrada no sistema, não automatizada; venda só pode ser concluída com status `aprovado`.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE11-IMPL-01, FASE5 (storage de documentos).
- **Resultado esperado:** tentativa de concluir venda sem crédito aprovado é bloqueada.
- **Critérios de aceite:** teste garante que uma venda não é criada para negociação com crédito `pendente`/`reprovado`.
- **Paralelizável:** Sim, com FASE11-IMPL-02.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E11.3 — Trilha de auditoria visível

### FASE11-IMPL-04 — Trilha de auditoria por lote na UI
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** gestor consegue ver, na tela de detalhe do lote, quem mudou preço/status e quando — sem precisar consultar o banco diretamente.
- **Descrição:** endpoint que lista entradas de `audit_log` filtradas por entidade `Lote`/`ReservaVenda` de um lote específico; tela no mobile/web (Fase 3/5) exibindo a lista ordenada por data.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** módulo `audit` da Fase 1 (já existe o dado, só falta expor).
- **Resultado esperado:** tela de auditoria funcional por lote.
- **Critérios de aceite:** uma mudança de preço de teste aparece na trilha com autor e timestamp corretos.
- **Paralelizável:** Sim, com FASE11-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE11-IMPL-01 (modelo de lead) → FASE11-IMPL-03 (aprovação de crédito).
- **Dev 2:** FASE11-IMPL-04 (trilha de auditoria, pode começar em paralelo) → FASE11-IMPL-02 (distribuição, depende do modelo de lead do Dev 1).
- **Pontos de sincronização:** schema de `Lead` (estágios possíveis, campos) combinado antes de FASE11-IMPL-02 e FASE11-IMPL-03 começarem, já que ambos dependem dele.
