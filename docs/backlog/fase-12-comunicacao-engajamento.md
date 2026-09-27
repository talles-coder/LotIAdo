# Fase 12 — Comunicação & Engajamento

Entrega desta fase: notificação de lead/negociação via WhatsApp, e favoritos internos (corretor marca lote de interesse do cliente) com alerta push de mudança de preço/status. O favorito de autosserviço do cliente final (ele mesmo favoritando pelo próprio app) fica para a Fase 14, quando o portal do cliente existir — aqui o favorito é sempre feito pelo corretor em nome do cliente, para não criar dependência circular com a Fase 14.

## Épico E12.1 — Fundamentos

### FASE12-EST-01-D1 / FASE12-EST-01-D2 — Estudo: WhatsApp Business Platform (Cloud API)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como enviar e receber mensagens via WhatsApp Business Platform (Cloud API oficial da Meta) sem custo para volume de demonstração.
- **Conceitos a entender:** cadastro de app de teste no Meta for Developers e número de teste (sandbox, sem custo); templates de mensagem (mensagens fora da janela de 24h exigem template pré-aprovado); janela de 24h de conversa (mensagem livre só dentro dela); webhook de mensagem recebida (payload, verificação de assinatura); diferença entre enviar notificação de sistema (template) e responder conversa (mensagem livre).
- **Material recomendado:** documentação oficial da Meta para WhatsApp Cloud API (Getting Started, Webhooks).
- **Exercício prático:** enviar uma mensagem de template de teste para o próprio número via sandbox e receber um webhook de resposta em um endpoint local (ex.: via túnel ngrok/similar).
- **Critério de conclusão:** mensagem de teste enviada e webhook de resposta recebido e logado.
- **Paralelizável:** Sim.

### FASE12-EST-02-D1 / FASE12-EST-02-D2 — Estudo: notificações push com Expo
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender o fluxo de notificação push do Expo de ponta a ponta.
- **Conceitos a entender:** `expo-notifications` (permissão do usuário, obtenção do push token); Expo Push API (envio de notificação a partir do backend usando o token); diferença de comportamento entre notificação em foreground/background; push não funciona no Expo for Web (D2) — a versão web precisa de um canal alternativo (ex.: apenas WhatsApp/e-mail, sem push nativo no navegador nesta fase).
- **Material recomendado:** documentação oficial do Expo sobre push notifications.
- **Exercício prático:** app de teste que obtém o push token, envia para um "backend" fake (script simples), e recebe notificação de volta via Expo Push API.
- **Critério de conclusão:** notificação de teste recebida no device/emulador.
- **Paralelizável:** Sim.

## Épico E12.2 — Integração WhatsApp

### FASE12-IMPL-01 — Notificação de mudança de estágio via WhatsApp
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** cliente recebe uma mensagem de WhatsApp quando seu lead muda de estágio relevante (ex.: crédito aprovado, contrato pronto).
- **Descrição:** serviço `WhatsAppNotifier` que envia mensagem de template via Cloud API quando o `Lead` (Fase 11) muda para estágios configurados; falha de envio não bloqueia a transição de estágio (log de erro, sem retry automático nesta fase).
- **Pré-requisitos:** FASE12-EST-01-D1.
- **Dependências:** FASE11-IMPL-01 (transições de estágio).
- **Resultado esperado:** transição de estágio configurada dispara mensagem real no sandbox de teste.
- **Critérios de aceite:** mudar um lead de teste para o estágio configurado gera uma mensagem visível no número de teste.
- **Paralelizável:** Sim, com FASE12-IMPL-02.
- **Conhecimentos novos introduzidos:** integração com API externa de mensageria, templates de mensagem.

### FASE12-IMPL-02 — Webhook de recebimento e histórico de conversa
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** mensagens recebidas de um lead ficam associadas a ele, visíveis para o corretor responsável — sem chatbot/resposta automática nesta fase.
- **Descrição:** endpoint de webhook que recebe mensagem do WhatsApp, identifica o `Lead` pelo número de telefone, e persiste como entrada de histórico de conversa vinculada.
- **Pré-requisitos:** FASE12-EST-01-D2.
- **Dependências:** FASE11-IMPL-01.
- **Resultado esperado:** mensagem recebida de um número de teste conhecido aparece no histórico do lead correspondente.
- **Critérios de aceite:** mensagem de um número não cadastrado é registrada sem vínculo (não quebra), e loga um aviso para tratamento manual.
- **Paralelizável:** Sim, com FASE12-IMPL-01.
- **Conhecimentos novos introduzidos:** consumo de webhook externo, verificação de assinatura de payload.

## Épico E12.3 — Favoritos e alertas

### FASE12-IMPL-03 — Favorito interno + alerta push de mudança de preço/status
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** corretor marca um lote como de interesse de um lead específico e recebe push quando o preço ou status do lote muda.
- **Descrição:** relação `Lead` ↔ `Lote` favoritado; job/trigger que, ao detectar mudança de preço/status em lote favoritado, envia push (Expo Push API) para o corretor responsável pelo lead.
- **Pré-requisitos:** FASE12-EST-02-D1.
- **Dependências:** FASE11-IMPL-01, FASE12-IMPL-01 (reaproveita o mesmo tipo de gatilho de notificação).
- **Resultado esperado:** mudança de preço de um lote favoritado gera push visível no app do corretor responsável.
- **Critérios de aceite:** teste garante que só o corretor responsável pelo lead (não todos) recebe o push.
- **Paralelizável:** Sim, com FASE12-IMPL-02.
- **Conhecimentos novos introduzidos:** Expo Push API a partir do backend.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE12-EST-01/02 → FASE12-IMPL-01 (WhatsApp saída) → FASE12-IMPL-03 (favoritos/push).
- **Dev 2:** FASE12-EST-01/02 → FASE12-IMPL-02 (WhatsApp entrada/webhook) → FASE12-IMPL-04 (painel de notificações).
- **Pontos de sincronização:** formato de `WhatsAppNotifier`/canal de notificação combinado entre Dev 1 e Dev 2 antes de FASE12-IMPL-01/03, já que os dois reaproveitam a mesma abstração de disparo de notificação; esse mesmo formato é a base do registro persistido em `FASE12-IMPL-04`.

## Épico E12.4 — Painel de notificações

### FASE12-IMPL-04 — Sino de notificações com histórico persistido
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** corretor/gestor não depende só do push (que pode não chegar, ser dispensado sem ler, ou ter sido enviado enquanto o app estava fechado) — existe um painel dentro do app com o histórico de eventos relevantes.
- **Descrição:** toda notificação disparada (push da Fase 12, alerta de favorito, WhatsApp recebido, mudança de estágio de lead da Fase 11, parcela vencida da Fase 13, etc.) também é persistida como registro de notificação in-app, associada ao usuário/tenant; ícone de sino no cabeçalho do app com contador de não-lidas; painel lista as notificações mais recentes primeiro, com marcação de lida/não-lida (individual e "marcar todas como lidas"); toda notificação nova de fase futura (financeiro, IA, etc.) reaproveita este mesmo mecanismo em vez de inventar um canal próprio — é o ponto único de "algo relevante aconteceu" dentro do app.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE12-IMPL-01/03 (primeiras fontes reais de notificação a alimentar o painel).
- **Resultado esperado:** notificação disparada de teste aparece no painel, com contador do sino atualizado; marcar como lida reflete imediatamente.
- **Critérios de aceite:** notificação de um tenant nunca aparece no sino de usuário de outro tenant (mesma defesa de isolamento já aplicada em todo o resto do sistema); contador do sino bate com a contagem real de não-lidas após qualquer ação (ler uma, marcar todas).
- **Paralelizável:** Não pode ser finalizada sem FASE12-IMPL-01 (ou stub do formato de notificação combinado antes).
- **Conhecimentos novos introduzidos:** nenhum além do já coberto na fase.
