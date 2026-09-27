# 04 — Roadmap (Etapa 4)

Ordem incremental, cada fase entrega uma versão funcional demonstrável. Backlog detalhado de cada fase em `docs/backlog/fase-N-*.md`.

| Fase | Nome | Entrega funcional | Depende de |
|---|---|---|---|
| 0 | Fundamentos & scaffolding | Repo, docker-compose com todos os serviços de base, skeleton FastAPI, módulos `tenancy`+`identity` mínimos, testes de setup | — |
| 1 | MVP núcleo de domínio (single tenant) | CRUD completo de loteamentos/lotes/clientes/corretores/reservas/vendas com máquina de estados e auditoria básica, via API (sem GIS, sem mobile) | Fase 0 |
| 2 | Multi-tenancy real | RLS aplicado de fato, múltiplos tenants de teste isolados, convite/ativação de usuários, RBAC evoluído | Fase 1 |
| 3 | Mobile MVP | App React Native consumindo a API (auth, listas, detalhes, criar reserva/venda) — valida a pilha mobile isoladamente, sem mapa/offline ainda | Fase 2 |
| 4 | GIS | PostGIS, polígonos, mapa no mobile e no backoffice, importação de CSV manual (sem IA) | Fase 2 (pode rodar em paralelo com Fase 3) |
| 5 | Backoffice web mínimo (Expo for Web) | Import CSV, editor/revisão de polígono, gestão de documentos — rotas web do mesmo app Expo | Fase 4 (parcialmente paralelizável com Fase 3/4 — ver Etapa 7 de cada backlog) |
| 6 | Offline read-cache no mobile | Cache local + detecção de conectividade + bloqueio de escrita offline | Fase 3 |
| 7 | Documentos + RAG | Upload, chunking, embeddings, pgvector, busca semântica com citação de fonte. Primeira introdução real de Redis/RQ como fila de processamento assíncrono (decisão D3) | Fase 5 (documentos já geridos no backoffice) |
| 8 | IA para importação flexível | CSV sem padrão fixo via LLM, extração assistida de planta/imagem, sempre com revisão humana | Fase 4 e Fase 5; a extração de imagem reaproveita a fila RQ/worker introduzida na Fase 7 |
| 9 | Agentes com LangGraph | Tools sobre os serviços existentes, chat no mobile/web | Fase 7 (RAG como uma das tools) |
| 10 | Observabilidade & Evaluation de IA | Logging estruturado, métricas, golden-set de avaliação para RAG/agentes | Fase 7 e Fase 9 |
| 11 | CRM Comercial & Funil de Vendas | Funil de leads com estágios, distribuição automática entre corretores, workflow de aprovação de crédito, trilha de auditoria por lote exposta na UI | Fase 1 (estados de reserva/venda) e Fase 2 (RBAC) |
| 12 | Comunicação & Engajamento | WhatsApp integrado (notificação/atendimento), favoritos com alerta de mudança de preço/status | Fase 11 (funil expõe lead/negociação) e Fase 3 (mobile) |
| 13 | Financeiro & Cobrança | Emissão de boleto/PIX via `PaymentProvider` abstrato, cobrança automática/régua de cobrança, assinatura eletrônica via provedor terceirizado, simulador de antecipação de recebíveis (educacional, sem operação financeira real) | Fase 11 (negociação gera contrato a cobrar) |
| 14 | Portal/App do Cliente Final (White-Label) | App/portal para o comprador acompanhar contrato/parcelas/documentos, comparador de lotes lado a lado, theming por tenant (logo/cor) | Fase 13 (dado financeiro a exibir) e Fase 5 (app único Expo) |
| 15 | GIS Avançado & Dados Abertos | Overlay de camadas públicas (zoneamento, APP, área de preservação), QR code físico no lote, exportação GeoJSON/CSV do loteamento | Fase 4 (GIS base) |
| 16 | Analytics & Precificação | Dashboard de velocidade de vendas/sazonalidade, precificação sugerida por comparáveis (heurística por vizinhança via PostGIS) | Fase 1 (histórico de vendas) e Fase 15 (dado geoespacial para comparáveis) |
| 17 | IA de Domínio Avançada | Agente de due diligence documental, copiloto "pergunte ao loteamento" isolado por tenant, relatório em linguagem natural via tools sobre serviços existentes (nunca texto-para-SQL direto), assistente de negociação (menor prioridade) | Fase 7 (RAG) e Fase 9 (Agentes LangGraph) |
| 18 | Internacionalização & Localização | Textos extraídos para arquivos de tradução (PT-BR como padrão, EN como segundo idioma de prova), seleção de idioma no app, formatação de moeda/data por locale | Fase 3 e Fase 5 (telas mobile/web já existentes para extrair texto) |
| 19 | Versionamento de API | Convenção de versionamento (`/v1/`, `/v2/`) aplicada com uma mudança incompatível real de exercício, para não deixar apps de campo desatualizados quebrarem sem aviso | Todas as fases de domínio anteriores (API já estável o suficiente para justificar v1) |
| 21 | Billing do SaaS & Autocadastro de Tenant | Modelo de plano/limites, autocadastro de imobiliária com seleção de plano, cobrança recorrente da assinatura via `PaymentProvider`, enforcement de limite de uso | Fase 2 (tenant) e Fase 13 (`PaymentProvider`) |
| 22 | Auditoria e Robustez de Formulários de Cadastro | Campos ausentes adicionados aos formulários de cliente/corretor/lote, validação de CPF (dígito verificador) e demais campos, alinhamento frontend/backend | Fase 1 (schemas Pydantic) e Fase 3 (telas mobile) |
| 23 | Estrutura de Testes (Unit/Integration/E2E) | Convenção de testes unitários/integração/E2E para backend e mobile, mocks padronizados, fixtures de ambiente, cobertura das fases 1–22 | Todas as fases de domínio e comerciais anteriores (testa o que já existe) |
| 24 | Cloud/produção (AWS) | Deploy, CI/CD, IaC básico | Todas as anteriores funcionando localmente |
| 25 | Segurança: Auditoria e Correção de Vulnerabilidades | Revisão de segurança de ponta a ponta (backend, mobile, infra) após o deploy em nuvem, correção de vulnerabilidades e más práticas encontradas | Fase 24 (sistema completo rodando, inclusive em nuvem) |

## Por que essa ordem

- **Domínio antes de GIS/mobile**: valida regras de negócio (estados, permissões, auditoria) antes de adicionar a complexidade de mapa e app mobile por cima.
- **Multi-tenancy antes de mobile/GIS**: isolamento de tenant é transversal — melhor testado cedo, antes de crescer a superfície de código que depende dele.
- **Mobile MVP sem mapa antes de GIS**: separa a validação da pilha mobile (auth, navegação, chamadas de API) da complexidade de mapa, permitindo os dois devs trabalharem em paralelo (um em GIS/backend, outro consolidando mobile) sem bloqueio mútuo.
- **RAG antes de Agentes**: o agente usa busca em documentos como uma de suas tools; construir RAG primeiro dá uma tool madura para o agente consumir.
- **Observabilidade por último entre os módulos de IA, não no fim do projeto**: entra logo depois de RAG e Agentes existirem (Fase 10), não é adiada até o final do roadmap inteiro.
- **Fases 11–17 (completude comercial) depois do núcleo técnico, antes de Cloud**: resultado da análise competitiva (`05-analise-competitiva.md`) — CRM/financeiro/portal do cliente/GIS avançado/IA de domínio só fazem sentido depois que domínio, multi-tenancy, mobile, GIS, offline, RAG e agentes já existem, porque reaproveitam esses alicerces em vez de duplicá-los (ex.: Fase 13 reaproveita o mesmo padrão de abstração `Provider` de D1/D4; Fase 17 reaproveita o RAG da Fase 7 e o agente da Fase 9).
- **i18n (Fase 18) e versionamento de API (Fase 19) por último, antes de Cloud**: ambos são transversais (tocam toda tela/endpoint já existente) — fazer isso cedo geraria retrabalho a cada fase nova; fazer depois de todo o domínio+comercial estar pronto extrai texto/estabiliza contrato uma única vez. SLA/uptime-alvo foi avaliado e **não** virou fase: é compromisso de negócio para cliente pagante, não uma feature de engenharia — para o portfólio fica documentado como "não definido" em `01-analise-requisitos.md`, sem task correspondente.
- **Fase 21 (Billing do SaaS) depois da Fase 13 (Financeiro)**: reaproveita o mesmo `PaymentProvider` para cobrar a assinatura da própria imobiliária, em vez de criar uma segunda integração de pagamento. Item que já estava registrado como "fora do escopo atual" em `01-analise-requisitos.md` (seção 2) e ganha fase formal aqui.
- **Fase 22 (formulários) antes da Fase 23 (testes)**: não faz sentido escrever testes abrangentes para formulários que ainda vão ganhar campo/validação nova — primeiro fecha o modelo de dados definitivo dos cadastros, depois cobre com teste.
- **Fase 23 (estrutura de testes) por último entre as fases de domínio, antes de Cloud**: consolida unit/integration/E2E sobre tudo que já existe (fases 0–22) de uma vez, em vez de impor um padrão de teste ainda instável a cada fase nova; é o portão de qualidade antes do deploy.
- **Cloud (Fase 24) antes da Segurança (Fase 25)**: princípio geral do projeto é rodar tudo localmente/gratuito primeiro; migrar para AWS só depois de tudo validado localmente evita gastar créditos/tempo de cloud iterando sobre algo que ainda pode mudar.
- **Segurança por último, de propósito**: pedido explícito do usuário — uma auditoria de segurança de ponta a ponta (incluindo a infraestrutura de nuvem já implantada na Fase 24) só é completa depois que todo o sistema, inclusive o deploy, existe. Isso não substitui boas práticas já aplicadas ao longo do caminho (RLS desde a Fase 2, defesa em profundidade em queries vetoriais, nunca texto-para-SQL na Fase 17) — é uma revisão final, não a primeira vez que segurança é considerada.
