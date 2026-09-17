# Fase 1 — MVP Núcleo de Domínio (single tenant)

Entrega desta fase: API funcional cobrindo loteamentos, lotes (com máquina de estados), clientes, corretores, reservas/vendas e auditoria básica — testável via `/docs` (Swagger). Ainda sem GIS/mapa (lotes têm localização opcional em lat/lng simples, sem polígono) e sem mobile. Assume-se um único tenant "de desenvolvimento" (multi-tenancy real só na Fase 2).

## Épico E1.1 — Regras de negócio: estados do lote

### FASE1-EST-01-D1 / FASE1-EST-01-D2 — Estudo: máquinas de estado finito para regras de negócio
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** saber modelar transições de estado válidas de forma explícita no domínio, em vez de checagens `if` espalhadas pelo código.
- **Conceitos a entender:** máquina de estados finita (estados, transições, guardas); onde colocar essa lógica em um módulo `domain` (função pura `pode_transicionar(de, para) -> bool` ou tabela de transições permitidas); idempotência de transição.
- **Material recomendado:** artigos introdutórios sobre "state machine pattern" em Python (não é necessário usar uma biblioteca de FSM, uma tabela/dicionário de transições permitidas já é suficiente para o escopo).
- **Exercício prático:** modelar em um script isolado a máquina de estados de um lote (ver tabela abaixo) e escrever testes que validam transições permitidas e proibidas.
- **Critério de conclusão:** exercício cobre todas as transições da tabela abaixo com testes verdes e as proibidas retornando erro.
- **Paralelizável:** Sim.

### Tabela de transições de estado do lote (decisão de negócio desta fase)

| De \ Para | disponível | reservado | vendido | bloqueado | inativo |
|---|---|---|---|---|---|
| disponível | — | ✅ | ❌ (precisa passar por reservado) | ✅ | ✅ |
| reservado | ✅ (cancelar reserva) | — | ✅ | ✅ | ❌ |
| vendido | ❌ | ❌ | — | ❌ | ✅ (só para arquivamento) |
| bloqueado | ✅ | ❌ | ❌ | — | ✅ |
| inativo | ✅ (reativar) | ❌ | ❌ | ❌ | — |

Regra: toda transição gera um registro de auditoria (quem, quando, de/para, motivo opcional). Reserva **não expira automaticamente** no MVP (simplificação registrada em [01-analise-requisitos.md](../01-analise-requisitos.md)) — cancelamento é uma ação manual explícita (transição reservado → disponível).

### FASE1-IMPL-01 — Módulo `loteamentos_lotes`: modelo de dados e máquina de estados
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** loteamentos e lotes persistidos, com transições de estado validadas pela tabela acima.
- **Descrição:** tabelas `loteamentos` (nome, descrição, tenant_id) e `lotes` (loteamento_id, identificação, quadra, área, preço, status, características em JSON, corretor_id nullable, cliente_id nullable); função de domínio que valida transição antes de persistir.
- **Pré-requisitos:** FASE1-EST-01-D1.
- **Dependências:** FASE0-IMPL-04 (tenancy), FASE0-IMPL-03 (skeleton).
- **Resultado esperado:** CRUD de loteamentos e lotes via API; transição de status só ocorre se válida.
- **Critérios de aceite:** teste cobre cada linha da tabela de transições (permitidas e proibidas); transição inválida retorna 409/422 com mensagem clara.
- **Paralelizável:** Sim, com FASE1-IMPL-02 (clientes/corretores), que não depende deste módulo.
- **Conhecimentos novos introduzidos:** máquina de estados em domínio Python puro.

## Épico E1.2 — Clientes e corretores

### FASE1-IMPL-02 — Módulos `clientes` e `corretores`: CRUD básico
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** cadastro básico de clientes e corretores, prontos para serem referenciados por reservas/vendas.
- **Descrição:** tabela `clientes` (nome, documento, contato, tenant_id); tabela `corretores` (nome, contato, usuário associado opcional, tenant_id). CRUD REST padrão para ambos.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE0-IMPL-04, FASE0-IMPL-03.
- **Resultado esperado:** CRUD de clientes e corretores funcionando via API.
- **Critérios de aceite:** testes de criação/listagem/atualização/remoção lógica (não hard-delete, ver auditoria) para ambos.
- **Paralelizável:** Sim, com FASE1-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E1.3 — Reservas e vendas

### FASE1-IMPL-03 — Módulo `vendas_reservas`: criar reserva, converter em venda, cancelar
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** operação central do produto — reservar um lote, converter em venda, ou cancelar — sempre movendo o status do lote junto (transação atômica).
- **Descrição:** tabela `reservas_vendas` (lote_id, cliente_id, corretor_id, tipo [reserva/venda], status, tenant_id, criado_em); ao criar reserva: valida que o lote está `disponível`, cria registro, transiciona lote para `reservado`, tudo em uma transação de banco; ao converter em venda: valida que está `reservado`, transiciona lote para `vendido`; ao cancelar: valida que está `reservado`, transiciona lote para `disponível`.
- **Pré-requisitos:** FASE1-EST-01 (herdado via FASE1-IMPL-01).
- **Dependências:** FASE1-IMPL-01, FASE1-IMPL-02.
- **Resultado esperado:** endpoints `POST /reservas`, `POST /reservas/{id}/converter-venda`, `POST /reservas/{id}/cancelar`.
- **Critérios de aceite:** teste garante atomicidade (se a transição de status falhar, a reserva não é criada, e vice-versa); teste garante que não é possível reservar um lote já reservado/vendido (concorrência básica via `SELECT ... FOR UPDATE` ou constraint de status).
- **Paralelizável:** Não pode começar antes de FASE1-IMPL-01 e FASE1-IMPL-02 estarem prontos (dependência direta de dados).
- **Conhecimentos novos introduzidos:** transação atômica multi-tabela, lock otimista/pessimista básico para evitar duas reservas simultâneas do mesmo lote (`SELECT FOR UPDATE`).

## Épico E1.4 — Auditoria

### FASE1-IMPL-04 — Módulo `audit`: trilha de auditoria imutável
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** toda ação sensível (transição de status, criação/cancelamento de reserva, venda, alteração de preço, alteração de responsável) fica registrada de forma imutável, sem depender de cada módulo lembrar de chamar algo manualmente.
- **Descrição:** tabela `audit_log` (append-only: sem UPDATE/DELETE permitido pela aplicação; ação, entidade, entidade_id, usuário, tenant_id, timestamp, payload antes/depois em JSON).
  - Auditoria é 100% declarativa, não há helper manual: `app.audit.infrastructure.tracking.rastrear_auditoria(...)`, um decorator aplicado uma única vez em cima do model (ex.: `Lote`, `ReservaVenda`), mapeia quais colunas são sensíveis para qual `AcaoAuditoria` (ou uma função `(antes, depois) -> AcaoAuditoria | None` quando a ação depende do valor novo, ex.: status de reserva virando "cancelada" vs "vendido"). Um listener de `before_flush` do SQLAlchemy (registrado globalmente, ativo em toda a aplicação) gera a entrada de `audit_log` sozinho sempre que um campo rastreado muda ou uma entidade marcada com `acao_criacao` é criada — nenhuma chamada dentro do service ou da rota. Se mais de um campo sensível mudar no mesmo flush e resolver para a mesma ação, viram uma única entrada com um payload combinando todos os campos, nunca uma linha por campo. Quem está autenticado na request (`usuario_id`/`tenant_id`) chega até o listener via `contextvars`, populados automaticamente pelo `AuditContextMiddleware` (registrado uma vez em `app.main`, não em cada rota).
  - Não existe (deliberadamente) uma via de escape manual — se surgir uma ação sensível cujo "antes/depois" não seja um diff de coluna (ex.: motivo digitado pelo usuário), aí sim vale adicionar um helper explícito; até lá seria código sem uso real (YAGNI).
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE0-IMPL-05 (identity, para saber quem é o usuário atual).
- **Resultado esperado:** todas as ações sensíveis de FASE1-IMPL-01/03 geram entrada em `audit_log`.
- **Critérios de aceite:** teste verifica que uma transição de status e uma criação de reserva geram exatamente uma entrada de auditoria cada, com o payload correto.
- **Paralelizável:** Sim, pode ser desenvolvido em paralelo com FASE1-IMPL-01/02/03 (ponto de sincronização: assinatura de `rastrear_auditoria(...)`, já implementada — Dev 1 só precisa decorar `Lote`/`ReservaVenda` ao criá-los).
- **Conhecimentos novos introduzidos:** padrão de log append-only/imutável; auditoria automática via eventos do ORM (`before_flush` + attribute history).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE1-EST-01 → FASE1-IMPL-01 (loteamentos/lotes) → FASE1-IMPL-03 (reservas/vendas, depende de IMPL-01 e IMPL-02).
- **Dev 2:** FASE1-IMPL-02 (clientes/corretores) → FASE1-IMPL-04 (auditoria).
- **Pontos de sincronização:**
  1. Auditoria de FASE1-IMPL-01/03 é automática (ver FASE1-IMPL-04): ao definir `Lote` e `ReservaVenda`, Dev 1 decora o model com `@rastrear_auditoria(entidade=..., acao_criacao=..., campos_sensiveis={...})` (já disponível em `app.audit.infrastructure.tracking`) — nenhuma chamada dentro do service.
  2. FASE1-IMPL-03 só integra de verdade depois que FASE1-IMPL-01 e FASE1-IMPL-02 exportarem seus repositórios/serviços — combinar a assinatura desses serviços (ex.: `LoteService.transicionar_status(...)`) antes de cada um implementar por completo, para evitar retrabalho de integração.
