# Fase 13 — Financeiro & Cobrança

Entrega desta fase: emissão de boleto/PIX por parcela de venda via **Asaas** (D11), cobrança automática de parcela vencida, assinatura eletrônica de contrato via **Autentique** (D12), e um simulador (não uma operação financeira real) de antecipação de recebíveis. Fecha as decisões D11 e D12 de `03-decisoes-tecnicas.md` — já resolvidas em 2026-09-27, as tasks de estudo abaixo são sobre a API do provedor escolhido, não mais uma comparação entre opções.

## Épico E13.1 — Fundamentos

### FASE13-EST-01-D1 / FASE13-EST-01-D2 — Estudo: gateway de pagamento Asaas (boleto/PIX) via API
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender o fluxo de emissão e confirmação de cobrança via a API do Asaas (D11), usando sandbox gratuito.
- **Conceitos a entender:** criação de cobrança (boleto e/ou PIX) via API do Asaas; webhook de confirmação de pagamento (evento assíncrono, não polling); ambiente sandbox vs. produção; idempotência (não gerar duas cobranças para a mesma parcela).
- **Material recomendado:** documentação oficial da API do Asaas (sandbox/ambiente de testes).
- **Exercício prático:** criar uma cobrança de teste no sandbox do Asaas, simular pagamento (o sandbox tem endpoint para isso) e receber o webhook de confirmação em endpoint local.
- **Critério de conclusão:** cobrança de teste emitida e confirmação recebida via webhook.
- **Paralelizável:** Sim.

### FASE13-EST-02-D1 / FASE13-EST-02-D2 — Estudo: assinatura eletrônica via API do Autentique
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender o fluxo de envio de documento para assinatura e confirmação de conclusão via a API do Autentique (D12), sem implementar assinatura com validade jurídica própria.
- **Conceitos a entender:** upload de documento e definição de signatário(s) via API do Autentique; link de assinatura enviado ao signatário; webhook de assinatura concluída; documento assinado (PDF final) disponibilizado para download.
- **Material recomendado:** documentação oficial da API do Autentique.
- **Exercício prático:** enviar um documento de teste para assinatura no nível gratuito do Autentique e receber o webhook de conclusão.
- **Critério de conclusão:** documento de teste assinado de ponta a ponta.
- **Paralelizável:** Sim.

## Épico E13.2 — Emissão e cobrança

### FASE13-IMPL-01 — `PaymentProvider` abstrato + emissão de boleto/PIX por parcela
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** cada parcela de uma venda pode ter uma cobrança emitida, sem acoplar o resto do sistema ao provedor escolhido.
- **Descrição:** interface `PaymentProvider` (mesmo padrão de `LLMProvider`/storage — decisões D1/D4) com implementação concreta para o provedor de D11; ao gerar a cobrança, persiste ID externo da cobrança e status (`pendente`/`pago`/`vencido`) na parcela.
- **Pré-requisitos:** FASE13-EST-01-D1.
- **Dependências:** FASE1 (modelo de venda/parcela), FASE11 (venda só existe após crédito aprovado).
- **Resultado esperado:** endpoint que emite cobrança para uma parcela existente, retornando link de pagamento/boleto.
- **Critérios de aceite:** parcela de teste tem cobrança emitida no sandbox do provedor com sucesso; trocar o provedor concreto não exige mudar nenhum código fora da implementação de `PaymentProvider`.
- **Paralelizável:** Sim, com FASE13-IMPL-03.
- **Conhecimentos novos introduzidos:** integração com gateway de pagamento real.

### FASE13-IMPL-02 — Webhook de confirmação de pagamento + régua de cobrança automática
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** status da parcela atualiza sozinho quando o pagamento é confirmado, e uma parcela vencida gera cobrança automática pelo canal já existente.
- **Descrição:** endpoint de webhook do provedor de pagamento, validando assinatura/origem antes de processar; job (reaproveitando o padrão RQ da Fase 7 se o volume justificar, ou execução direta se simples o suficiente) que verifica parcelas vencidas e dispara notificação via `WhatsAppNotifier`/push (Fase 12).
- **Pré-requisitos:** FASE13-EST-01-D2.
- **Dependências:** FASE13-IMPL-01, FASE12 (canal de notificação).
- **Resultado esperado:** pagamento simulado no sandbox atualiza a parcela para `pago` automaticamente; parcela vencida de teste gera notificação.
- **Critérios de aceite:** teste garante que o webhook só processa se a assinatura/origem for válida (rejeita payload forjado).
- **Paralelizável:** Não pode ser finalizada sem FASE13-IMPL-01.
- **Conhecimentos novos introduzidos:** validação de webhook externo, régua de cobrança.

## Épico E13.3 — Assinatura eletrônica

### FASE13-IMPL-03 — Envio de contrato para assinatura eletrônica
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** contrato de venda é enviado para assinatura do cliente e o status fica visível no sistema.
- **Descrição:** ao concluir a venda (crédito aprovado, Fase 11), documento de contrato (gerado ou já existente no storage da Fase 5) é enviado ao provedor de assinatura escolhido em D12; webhook de conclusão marca o contrato como assinado e disponibiliza o PDF final no storage.
- **Pré-requisitos:** FASE13-EST-02-D1.
- **Dependências:** FASE11-IMPL-03 (crédito aprovado), FASE5 (storage de documentos).
- **Resultado esperado:** contrato de teste enviado e assinado de ponta a ponta no sandbox.
- **Critérios de aceite:** status do contrato reflete corretamente `enviado`/`assinado`; PDF assinado fica acessível via storage.
- **Paralelizável:** Sim, com FASE13-IMPL-01.
- **Conhecimentos novos introduzidos:** integração com API de assinatura eletrônica.

## Épico E13.4 — Simulador de antecipação de recebíveis

### FASE13-IMPL-04 — Calculadora educacional de antecipação de recebíveis
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** demonstrar o conceito de antecipação de recebíveis sem operar uma transação financeira real.
- **Descrição:** dado um conjunto de parcelas futuras de um tenant, calcula o valor líquido "se antecipado" com uma taxa de desconto configurável (fórmula de valor presente simples); UI deixa explícito que é uma simulação/estudo, sem nenhuma integração com fomento/factoring real — **não** processa nem promete um pagamento antecipado de verdade.
- **Pré-requisitos:** nenhum estudo novo.
- **Dependências:** FASE13-IMPL-01 (parcelas com cobrança já existem).
- **Resultado esperado:** tela/endpoint que retorna o valor simulado para uma carteira de parcelas escolhida.
- **Critérios de aceite:** cálculo confere com uma fórmula de valor presente validada manualmente para um caso de teste.
- **Paralelizável:** Sim, com qualquer outra task da fase.
- **Conhecimentos novos introduzidos:** nenhum (cálculo financeiro simples).

## Divisão de trabalho e sincronização

- **Dev 1:** FASE13-EST-01/02 → FASE13-IMPL-01 (`PaymentProvider`) → FASE13-IMPL-03 (assinatura eletrônica).
- **Dev 2:** FASE13-EST-01/02 → FASE13-IMPL-02 (webhook/régua de cobrança) → FASE13-IMPL-04 (simulador de antecipação).
- **Pontos de sincronização:** interface de `PaymentProvider` (métodos, formato de retorno) combinada antes de FASE13-IMPL-02 poder ser desenvolvida em paralelo com stub.
