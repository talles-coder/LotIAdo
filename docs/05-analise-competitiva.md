# 05 — Análise Competitiva (Etapa 5)

> Levantamento feito em 2026-09-27 para identificar concorrentes diretos/indiretos do LotIAdo e decidir, com critério, o que entra no roadmap como consequência (não "feature por feature" sem avaliar ganho real). Resultado das decisões: ver `04-roadmap.md` (Fases 11–17) e a seção 2 de `01-analise-requisitos.md` (itens que estavam "fora do escopo atual" e agora têm fase definida).

## Concorrentes diretos (Brasil — mesmo nicho de loteamento)

| Produto | Foco | O que têm que o LotIAdo não tinha |
|---|---|---|
| [Lote Mobile](https://www.lotemobile.com.br/) | Mapa interativo, CRM, financeiro, app white-label | App white-label pro cliente final (contrato/parcela/documento), boleto com taxa zero, cobrança automática |
| [SIVI](https://sivi.app.br/) | Gestão de loteamento desde 2005, >500 mil lotes | Maturidade/escala comercial, não tecnologia |
| [Sistema SGL](https://sistemasgl.com.br/) | ERP com funil, distribuição de leads, aprovação de crédito | Funil de leads com distribuição automática (“roleta”), workflow de aprovação de crédito |
| [LOTEAR](https://www.sistemalotear.com.br/) | Espelho de vendas sobre Google Maps | Nada superior tecnicamente (mapa mais simples que o PostGIS/MapLibre do LotIAdo) |
| [Lotewin](https://www.lotewin.com.br/) | Gestão comercial/financeira | Similar ao SGL |
| [trilote](https://trilote.com/) | ERP + CRM de cobrança, pós-venda, antecipação de recebíveis, assinatura eletrônica | Antecipação de recebíveis (produto financeiro), assinatura eletrônica nativa |
| [LotNet](https://www.lotnet.com.br/) | Mapa interativo + "IA" + simulador de pagamento | IA no fluxo (provável chatbot de terceiro, não RAG/agentes locais) |
| [LoteMap](https://lotemap.com.br/) | Só a camada de mapa interativo | Nicho — não é ERP completo |
| [CV CRM](https://cvcrm.com.br/cv-para-loteadora/) / [Jetimob](https://www.jetimob.com/crm-loteadora) | CRM imobiliário genérico com módulo de loteadora | Base grande de integrações com portais de anúncio |
| [Imobzi](https://www.imobzi.com/) | ERP com cobrança recorrente e inadimplência em tempo real | Cobrança recorrente nativa integrada a banco |

## Concorrentes internacionais (land development software)

| Produto | Diferencial |
|---|---|
| [LotVue (ECI Solutions)](https://www.ecisolutions.com/industries/residential-construction/land-developers/) | Reserva/alocação de lotes em colaboração com construtoras (mercado de incorporação em massa, EUA) |
| [Lotizacion](https://lotizacion.com/real-estate-land-software) | Mapa + reservas + pagamentos + financiamento in-house |
| [Groov](https://letsgroov.com/) | Mapa de lotes embeddable no site do loteador |
| [Elevate (Acumatica)](https://www.elevatesolutionsre.com/land-development-software/) | Controle financeiro por fase de obra (takedown schedules) — nível de ERP de construção que nenhum concorrente brasileiro do nicho tem |

## Onde nenhum concorrente do nicho chega perto

- **IA local (Ollama) via `LLMProvider`** — os que citam "IA" (LotNet e ferramentas genéricas de CRM imobiliário como Morada.ai) usam API de terceiro para qualificação de lead. Nenhum oferece RAG/agentes rodando 100% local.
- **Privacidade como argumento comercial**: dado do cliente (CPF, renda, documento) nunca sai do servidor do tenant — decorre da decisão já tomada de ambiente de IA CPU-only/local (`01-analise-requisitos.md`, seção 1, item 3), não é feature nova, é um diferencial a **documentar** explicitamente.
- **PostGIS + pgvector com RLS multi-tenant** — concorrentes usam Google Maps embed (LOTEAR) em vez de GIS nativo com camadas de restrição legal.
- **App único mobile + web (Expo)** — concorrentes têm apps separados para corretor e painel admin.

## Funcionalidades de mercado incorporadas ao roadmap (validadas)

Critério aplicado: só entra se resolve um problema real de uso (não "feature a mais"). Foram então distribuídas em fases novas — ver `04-roadmap.md`:

| Funcionalidade do mercado | Fase destino | Nota de escopo |
|---|---|---|
| CRM com funil de leads | Fase 11 | Reaproveita máquina de estados de reserva/venda já existente (Fase 1) |
| Distribuição automática de leads entre corretores | Fase 11 | Round-robin simples primeiro, não otimização de IA |
| Aprovação de crédito | Fase 11 | Workflow de status manual (não integração de bureau de crédito — fora de escopo de portfólio) |
| WhatsApp integrado | Fase 12 | Canal de notificação/atendimento, não substitui o CRM |
| Favoritos com alerta de preço/status | Fase 12 | Depende do portal do cliente (Fase 14) existir |
| Emissão de boleto/PIX | Fase 13 | Via `PaymentProvider` abstrato (mesmo padrão de `LLMProvider`/storage), não banco direto |
| Cobrança automática/recorrente | Fase 13 | Régua de cobrança sobre o `PaymentProvider`, não integração bancária própria |
| Assinatura eletrônica | Fase 13 | Integração com provedor terceirizado (Clicksign/D4Sign/Autentique) — assinatura com validade jurídica própria (ICP-Brasil) é fora de escopo de portfólio |
| Antecipação de recebíveis | Fase 13 | **Rebaixado para simulador/calculadora educacional** — é um produto financeiro real (fomento/factoring), não uma feature de software; construir a operação de verdade não cabe no escopo de portfólio |
| App white-label pro cliente final | Fase 14 | Theming por tenant (logo/cor), reaproveitando o app Expo único já existente — não é um segundo app |

**Descartado sem rebaixamento**: nenhum item foi descartado por completo — "taxa zero" no boleto (Lote Mobile) não é uma feature técnica, é um modelo comercial de parceria com gateway de pagamento; não se aplica a um projeto de portfólio e não vira task.

## Ideias próprias validadas (do brainstorm simples → avançado)

| Ideia | Fase destino | Por que entrou |
|---|---|---|
| Trilha de auditoria por lote | Fase 11 (expande auditoria já existente da Fase 1) | Já existe auditoria básica; só falta expor a trilha de mudança de preço/status na UI |
| Comparador de lotes lado a lado | Fase 14 | Baixa complexidade, uso real no momento de decisão do cliente |
| QR code na placa física do lote | Fase 15 | Baixa complexidade, ganho prático real em campo |
| Exportação GeoJSON/CSV do loteamento | Fase 15 | Due diligence e integração externa — dado já existe no PostGIS |
| Overlay de camadas GIS públicas (zoneamento, APP, área de preservação) | Fase 15 | Alto valor (reduz risco jurídico), mas depende de disponibilidade de dado público por município — risco de cobertura desigual registrado como risco da fase |
| Dashboard de velocidade de vendas/sazonalidade | Fase 16 | BI simples sobre dados que já existem desde a Fase 1 |
| Precificação sugerida por comparáveis | Fase 16 | Começa como heurística (preço médio/m² por vizinhança via PostGIS), não ML — modelo preditivo fica para depois se o heurístico não for suficiente |
| Agente de due diligence documental | Fase 17 | Uso direto do RAG (Fase 7) sobre documento real (memorial, matrícula, licença) |
| Copiloto "pergunte ao loteamento" | Fase 17 | Extensão natural do agente da Fase 9, isolado por tenant |
| Relatório em linguagem natural | Fase 17 | **Importante:** implementado como tool que chama serviços/queries já existentes, nunca texto-para-SQL direto contra o banco — texto-para-SQL bypassa RLS e é risco de segurança, não só de qualidade |
| Assistente de negociação (sugestão de resposta pro corretor) | Fase 17 | Menor prioridade dentro da fase — valor real mas difícil de avaliar objetivamente (qualidade subjetiva); entra como último item da fase |

## Adendo (2026-09-27): itens pedidos diretamente pelo usuário, fora da análise competitiva

Quatro itens abaixo não vieram do levantamento de concorrentes, vieram de feedback direto do usuário depois de revisar o roadmap expandido — registrados aqui para manter a regra de "nunca 'como conversamos anteriormente'" do `CLAUDE.md`:

- **SCRUM-123** ("Autocadastro de imobiliária com seleção de plano de assinatura") já existia no Jira, criada fora do padrão (sem épico pai, sem `FASEN-IMPL-xx` no título, label `sem-fase`) por outra sessão. Trazida para o padrão: virou `FASE21-IMPL-02`, sob o épico `E21.2`, no Jira e no backlog (`fase-21-billing-saas.md`).
- **Estrutura de testes** (Fase 23): usuário observou que a base de testes existente (só backend, pytest) precisa virar uma convenção real de unit/integration/E2E nas duas pontas (backend + mobile), com mocks e setup de ambiente pensados, não só mais testes soltos.
- **Robustez de formulários de cadastro** (Fase 22): usuário notou que os formulários de cliente/corretor/lote parecem simples demais (poucos campos) e pediu auditoria de quais campos faltam e se as validações existentes (CPF, etc.) são de fato robustas (dígito verificador, não só formato).
- **Auditoria de segurança** (Fase 25): usuário pediu uma fase dedicada a buscar vulnerabilidades e más práticas **depois que tudo mais existir**, incluindo o deploy em nuvem da Fase 24 — não substitui as práticas de segurança já aplicadas ao longo do roadmap (RLS desde a Fase 2, filtro de tenant explícito em busca vetorial, proibição de texto-para-SQL na Fase 17), é uma revisão final.

## Adendo 2 (2026-09-27): revisão de detalhe pelo usuário, sete pontos

Depois de revisar o roadmap expandido, o usuário pediu sete ajustes de detalhe, todos incorporados nas fases correspondentes:

1. **White-label não tinha task de configuração**: `FASE14-IMPL-04` só aplicava tema, ninguém coletava logo/nome/cor. Criada `FASE14-IMPL-05` (tela de configuração de identidade visual), reaproveitada no autocadastro (`FASE21-IMPL-02`).
2. **Animações/partículas na tela de login**: nova **Fase 26** (Polimento Visual & Microinterações), com portão de aprovação humana explícita via GIF antes de qualquer integração real — pedido explícito de cautela do usuário.
3. **Termo de uso**: `FASE21-IMPL-05`, aceite obrigatório no autocadastro, com nota de que o texto jurídico em si não substitui revisão de advogado se isso virar produto real.
4. **Preços dos planos**: seção "Planos propostos" em `fase-21-billing-saas.md`, calibrada por levantamento de mercado (CRMs imobiliários genéricos brasileiros, já que concorrentes diretos do nicho não publicam preço).
5. **Autocomplete de CEP/selects fechados/foto de usuário**: `FASE22-IMPL-05` (ViaCEP + IBGE + select de UF/país) e `FASE22-IMPL-06` (avatar do usuário, distinto do logo do tenant).
6. **Painel de notificações (sino)**: `FASE12-IMPL-04`, histórico persistido além do push, reaproveitando o mesmo formato de notificação já usado no canal WhatsApp/push.
7. **Botão de ajuda/suporte com IA**: `FASE17-IMPL-07`, escopo deliberadamente separado do copiloto de negócio (`FASE17-IMPL-02`) para não confundir "dúvida sobre o app" com "dúvida sobre o loteamento".

Nessa mesma revisão o usuário também fechou as decisões D11–D14, D16 e D17 (ver `03-decisoes-tecnicas.md`), incluindo uma mudança real de abordagem em D14 (versionamento por **header**, não path, como o rascunho original sugeria) — o backlog da Fase 19 foi reescrito para refletir isso.

## Consequência em outros documentos

- `01-analise-requisitos.md`, seção 2: itens que estavam listados como "fora do escopo atual" (fluxo financeiro, CRM/funil, notificações, LGPD) agora apontam para a fase correspondente.
- `03-decisoes-tecnicas.md`: novas decisões em aberto D11 (provedor de pagamento/boleto) e D12 (provedor de assinatura eletrônica).
- `04-roadmap.md`: Fases 11–17 inseridas antes da Fase Cloud; Fases 18 (i18n) e 19 (versionamento de API) adicionadas em seguida; Fases 21 (billing do SaaS), 22 (formulários) e 23 (testes) adicionadas depois do adendo acima; Cloud passa a ser Fase 24 (`docs/backlog/fase-24-cloud-producao.md`); Fase 25 (segurança) fecha o roadmap.
