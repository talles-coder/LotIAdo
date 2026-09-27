# Fase 21 — Billing do SaaS & Autocadastro de Tenant

Entrega desta fase: uma imobiliária se autocadastra como tenant escolhendo um plano, o plano define limites de uso (usuários/loteamentos), e a assinatura do próprio plano é cobrada recorrentemente via o mesmo `PaymentProvider` já construído na Fase 13 — sem criar uma segunda integração de pagamento. Fecha o item "Modelo de planos/limites do próprio SaaS", registrado como fora de escopo em `01-analise-requisitos.md` (seção 2) desde a análise inicial.

## Planos propostos (preços em BRL)

Levantamento de mercado (2026-09-27) para calibrar preço: CRMs imobiliários genéricos no Brasil variam de ~R$75/mês (entrada, ex. ImobiBrasil) a ~R$250/mês (ex. Kenlo Prime, Jetimob) em planos publicados; concorrentes diretos do nicho de loteamento (Sistema SGL, CV CRM, Lote Mobile) não publicam preço — vendem sob proposta customizada, prática comum em B2B de nicho estreito. Critério usado: ficar competitivo com o CRM genérico (não fugir da faixa de mercado), mas se diferenciar por trazer recursos que só aparecem em plano caro de concorrente genérico (IA, GIS avançado) já no plano intermediário.

| Plano | Preço mensal | Preço anual (equivalente/mês) | Limites (`FASE21-IMPL-01`) | O que inclui além do núcleo |
|---|---|---|---|---|
| **Starter** | R$ 149 | R$ 129 (cobrado anual) | 3 usuários, 1 loteamento, até 150 lotes | Domínio + GIS básico + mobile (Fases 0–6) |
| **Pro** | R$ 349 | R$ 299 (cobrado anual) | 10 usuários, 5 loteamentos, até 1.500 lotes | + CRM/funil, WhatsApp, financeiro/cobrança, RAG (Fases 7, 11–13) |
| **Enterprise** | R$ 799 | R$ 699 (cobrado anual) | Usuários/loteamentos ilimitados (uso justo) | + Agentes de IA, portal white-label do cliente, analytics, suporte prioritário (Fases 9, 14, 16, 17) |

Notas de calibragem: preço abaixo do Starter (ex. R$ 50-80) tende a não cobrir nem o custo de suporte de um SaaS B2B nesse nicho, mesmo pequeno; preço do Enterprise fica deliberadamente abaixo do que concorrentes cobrariam sob proposta customizada (que tende a passar de R$1.000+/mês para loteadoras médias/grandes) — o objetivo aqui é parecer atrativo para portfólio, não maximizar receita. Esses valores alimentam o seed de `FASE21-IMPL-01` (não são um cálculo definitivo de unit economics real — não há custo de infraestrutura/suporte real medido para validar precificação de produção).

## Épico E21.1 — Modelo de planos e limites

### FASE21-IMPL-01 — Modelo de plano (limites de uso) e associação a tenant
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** todo tenant tem um plano associado, e o plano define limites objetivos (nº de usuários, nº de loteamentos, nº de lotes).
- **Descrição:** entidade `Plano` (nome, preço, limites) e relação 1:1 com `Tenant` (Fase 0); planos iniciais cadastrados via seed/migration com os valores da seção "Planos propostos" acima (Starter/Pro/Enterprise) — sem UI de administração de planos nesta fase, só o modelo de dados e os valores fixos.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE0-IMPL-04 (modelo de `Tenant`).
- **Resultado esperado:** tenant de teste tem plano associado com limites consultáveis via API.
- **Critérios de aceite:** consulta ao tenant retorna o plano e seus limites corretamente.
- **Paralelizável:** Sim, com FASE21-IMPL-04 (que consome este modelo, mas pode ser desenhada em paralelo com contrato combinado).
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E21.2 — Autocadastro e billing do tenant

### FASE21-IMPL-02 — Autocadastro de imobiliária (tenant) com seleção de plano de assinatura
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** uma imobiliária nova se cadastra sozinha no sistema, sem depender de um admin criar o tenant manualmente, escolhendo um dos planos disponíveis.
- **Descrição:** fluxo público de cadastro (fora de qualquer tenant autenticado) que cria `Tenant` + `Plano` escolhido + primeiro usuário administrador do tenant, reaproveitando o cadastro de usuário já existente (Fase 0/2); tela de seleção de plano no app (mobile/web) mostrando os planos e seus limites (valores da seção "Planos propostos"); ao final do cadastro, oferece (como etapa opcional, "pular por agora") a mesma tela de identidade visual de `FASE14-IMPL-05` (logo/nome de exibição/cor), para a imobiliária já sair com o app com a cara dela desde o primeiro acesso; aceite obrigatório do termo de uso (`FASE21-IMPL-05`) antes de concluir.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE21-IMPL-01, FASE2 (RBAC/convite de usuário), FASE14-IMPL-05 (tela de identidade visual, reaproveitada aqui), FASE21-IMPL-05 (termo de uso).
- **Resultado esperado:** cadastro de teste cria tenant novo, plano associado e usuário admin funcional, sem intervenção manual; opcionalmente já com logo/cor configurados.
- **Critérios de aceite:** tenant recém-criado já está isolado (RLS) e funcional para login imediato do admin criado; pular a etapa de identidade visual não bloqueia o cadastro (fallback visual padrão aplicado).
- **Paralelizável:** Não pode ser finalizada sem FASE21-IMPL-01.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em multi-tenancy (Fase 2).

### FASE21-IMPL-03 — Cobrança recorrente da assinatura do plano
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** a mensalidade do plano do tenant é cobrada automaticamente, reaproveitando o gateway de pagamento já integrado.
- **Descrição:** job periódico que gera uma cobrança (boleto/PIX) via `PaymentProvider` (Fase 13) para cada tenant ativo, no valor do plano escolhido; webhook de confirmação (já existente na Fase 13) atualiza o status de pagamento da assinatura do tenant.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE21-IMPL-01, FASE13-IMPL-01/02 (`PaymentProvider` e webhook já existentes).
- **Resultado esperado:** cobrança mensal de teste gerada e confirmada via sandbox, atualizando o status de assinatura do tenant.
- **Critérios de aceite:** dois tenants com planos diferentes geram cobranças com valores corretos correspondentes a cada plano.
- **Paralelizável:** Sim, com FASE21-IMPL-04.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em pagamento (Fase 13).

### FASE21-IMPL-04 — Enforcement de limite de uso do plano
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** um tenant não consegue ultrapassar os limites do próprio plano (ex.: criar mais usuários ou loteamentos do que o contratado) sem um aviso claro.
- **Descrição:** verificação de limite antes de criar usuário/loteamento (ou outra entidade limitada pelo plano), retornando erro de negócio claro (não erro genérico) quando o limite é atingido; nenhuma ação automática de upgrade — só bloqueio com mensagem.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE21-IMPL-01.
- **Resultado esperado:** tentativa de criar usuário/loteamento além do limite do plano de teste é bloqueada com mensagem clara.
- **Critérios de aceite:** teste garante que o limite é reavaliado a cada tentativa (não cacheado indevidamente) e que tenants de planos diferentes têm limites distintos aplicados corretamente.
- **Paralelizável:** Sim, com FASE21-IMPL-03.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E21.3 — Termo de uso e privacidade

### FASE21-IMPL-05 — Termo de uso e política de privacidade + aceite obrigatório no autocadastro
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** existe um termo de uso e uma política de privacidade reais (não placeholder), e ninguém cria conta sem aceitar formalmente.
- **Descrição:** documento de Termo de Uso (relação LotIAdo ↔ imobiliária cliente do SaaS) e Política de Privacidade (tratamento de dado pessoal de cliente/corretor/cliente-final, cobrindo os CPFs e contatos coletados desde a Fase 1 e ampliados na Fase 22 — LGPD) escritos em linguagem simples, versionados (campo `versao_termo_aceito` no registro do usuário/tenant); checkbox de aceite obrigatório (não pré-marcado) no autocadastro, bloqueando o fluxo sem ele; se o termo mudar de versão, usuário existente é obrigado a reaceitar no próximo login antes de continuar usando o sistema. **Nota:** o texto jurídico em si (redação com validade legal) está fora do que este projeto de portfólio garante — o conteúdo inicial é um rascunho razoável, não substitui revisão por advogado se isso um dia virar produto real.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE0 (modelo de usuário/tenant).
- **Resultado esperado:** autocadastro (`FASE21-IMPL-02`) não conclui sem o aceite; termo é consultável a qualquer momento pelo usuário logado.
- **Critérios de aceite:** tentativa de cadastro sem marcar aceite é bloqueada; mudar a versão do termo força reaceite de usuário existente no próximo login (testado com um usuário de fixture já aceito na versão anterior).
- **Paralelizável:** Sim, com FASE21-IMPL-01/03/04.
- **Conhecimentos novos introduzidos:** nenhum.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE21-IMPL-01 (modelo de plano) → FASE21-IMPL-03 (cobrança recorrente).
- **Dev 2:** FASE21-IMPL-05 (termo de uso, pode começar em paralelo) → FASE21-IMPL-02 (autocadastro, depende do modelo do Dev 1 e do termo) → FASE21-IMPL-04 (enforcement de limite).
- **Pontos de sincronização:** schema de `Plano` (campos de limite, nomes dos planos) combinado antes de FASE21-IMPL-02 e FASE21-IMPL-04 avançarem em paralelo com o Dev 1; formato de dado de identidade visual combinado com quem implementar `FASE14-IMPL-05` antes de `FASE21-IMPL-02` reaproveitá-lo.

## Nota de rastreabilidade

A implementação de `FASE21-IMPL-02` já existia como issue solta no Jira (criada fora do padrão por outra sessão, sem épico pai nem convenção de título) antes desta fase ser formalizada — foi trazida para o padrão (renomeada, associada ao épico `E21.2`, labels ajustadas) em vez de duplicada.
