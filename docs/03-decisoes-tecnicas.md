# 03 — Decisões Técnicas (Etapa 3)

Formato por decisão: opções, vantagens, desvantagens, custo, impacto no aprendizado, recomendação. As 4 decisões bloqueantes (backoffice web, isolamento multi-tenant, ambiente de IA, offline) já foram fechadas com o usuário e estão em [01-analise-requisitos.md](01-analise-requisitos.md) — não repetidas aqui. **D1–D18 abaixo já foram decididas com o usuário** (resultado marcado em cada uma), exceto D6, D15 e D18, que ficam deliberadamente em aberto até o momento indicado em cada uma (D6 depende de estudo prático na Fase 7; D15 e D18 dependem de teste prático nas Fases 16 e 26). D8 foi adicionada como consequência direta da decisão D2; D11–D18 vieram da análise competitiva/expansão de roadmap em [05-analise-competitiva.md](05-analise-competitiva.md), com D11–D14, D16 e D17 fechadas em 2026-09-27.

## D1 — Autenticação e RBAC — ✅ Decidido: (A) Construir mínimo

**Opções:**
- (A) Construir mínimo: JWT emitido pelo backend + tabelas de papel/permissão próprias.
- (B) Biblioteca `fastapi-users`.
- (C) Keycloak (Identity Provider dedicado).

| | (A) Mínimo próprio | (B) fastapi-users | (C) Keycloak |
|---|---|---|---|
| Vantagens | Aprendizado direto de JWT/RBAC/hash de senha; controle total do modelo de permissões; zero infraestrutura extra | Menos código para escrever; recursos prontos (reset de senha, verificação de e-mail) | Padrão de mercado, suporta SSO/OAuth de terceiros, UI de administração pronta |
| Desvantagens | Mais código para escrever e manter | Menos aprendizado sobre os fundamentos; RBAC multi-tenant customizado exige adaptação | Infraestrutura extra (outro serviço rodando), overhead para o escopo do MVP |
| Custo | Zero | Zero | Zero (self-hosted), mas custo operacional |
| Impacto no aprendizado | Alto (auth/RBAC é conteúdo central para portfólio) | Médio | Baixo para o objetivo do projeto (aprender a integrar, não a implementar) |

**Recomendação:** (A) Construir mínimo. RBAC com papéis multi-tenant é justamente um dos temas que o projeto quer ensinar; Keycloak adiciona infraestrutura sem esse ganho de aprendizado no momento.

## D2 — Stack do backoffice web — ✅ Decidido: (C) Expo for Web, no mesmo repositório do app

O usuário optou por uma terceira via, não cogitada nas opções originais: usar o próprio app React Native + Expo para também gerar a versão web (Expo for Web / React Native Web), em vez de um backend server-rendered ou uma SPA React separada.

**Opções (registro histórico):**
- (A) Server-rendered: FastAPI + Jinja2 + HTMX.
- (B) SPA separada: React + Vite (novo frontend, nova stack de build/deploy).
- (C) Expo for Web: o mesmo código do app mobile compilado para web pelo Expo — **escolhida**.

| | (A) Server-rendered | (B) SPA separada | (C) Expo for Web |
|---|---|---|---|
| Vantagens | Reaproveita o backend; sem build de frontend separado | Mais rico para interações complexas | Um único código-fonte para mobile e web: mesma autenticação, mesmos tipos, mesmos componentes de domínio (listas, formulários) reaproveitados; backend fica só API REST pura, sem módulo de interface a mais |
| Desvantagens | HTMX é tecnologia nova; interações ricas (mapa) exigem JS à parte de qualquer forma | Duplica stack de frontend só para telas administrativas | Bibliotecas nativas (mapa, secure storage) não funcionam automaticamente na web — exige implementação por plataforma (ver D8); Expo for Web é menos maduro/documentado que Expo nativo |
| Custo | Zero | Zero | Zero |
| Impacto no aprendizado | Médio (HTMX) | Baixo incremental | Alto — expõe na prática os limites de "write once, run everywhere" em React Native, e ensina o padrão de abstração por plataforma (`.native.tsx`/`.web.tsx`), útil também fora deste projeto |

**Consequência arquitetural:** o backend não precisa de nenhum módulo de interface server-rendered — simplificação líquida em relação ao plano anterior. O custo passa a ser inteiramente do lado do app Expo (resolver mapa e storage por plataforma — ver D8 e a Fase 5 do backlog).

## D3 — Jobs assíncronos para ingestão de IA — ✅ Decidido: (B) Redis + fila de jobs, desde a Fase 7

O usuário optou por já usar Redis com uma fila de jobs real desde que houver a primeira necessidade concreta de processamento assíncrono, em vez de adiar para quando o processamento ficasse pesado — explicitamente para estudar Redis na prática, não só como decisão de escala.

**Opções (registro histórico):**
- (A) `FastAPI BackgroundTasks` (processamento simples em background, sem fila persistente).
- (B) Celery ou RQ + Redis (fila de jobs persistente, com retry) — **escolhida**, especificamente **RQ** (Redis Queue): API mais simples que Celery, adequada ao porte do projeto e a um primeiro contato prático com fila/worker sobre Redis.

| | (A) BackgroundTasks | (B) RQ + Redis |
|---|---|---|
| Vantagens | Zero infraestrutura extra; simples de entender e testar | Retry automático, fila persistente sobrevive a restart, escala para processamento pesado; ensina Redis como broker de fila na prática (objetivo explícito do usuário) |
| Desvantagens | Job perdido se o processo reiniciar no meio; não é adequado para processamento realmente pesado/demorado | Mais uma peça de infraestrutura (worker RQ) para operar |
| Custo | Zero | Zero (self-hosted) |
| Impacto no aprendizado | Baixo | Médio-alto (filas, workers, idempotência) |

**Onde entra no roadmap:** a primeira necessidade real de processamento assíncrono é o pipeline de chunking + embeddings da **Fase 7** (chamadas a um LLM local podem ser lentas — ver decisão sobre ambiente de IA CPU-only), não mais a Fase 8 como cogitado inicialmente. A Fase 8 (extração de imagem, ainda mais pesada) reaproveita a mesma fila RQ já existente. Import de CSV (Fase 4) continua síncrono — volume pequeno o suficiente para não justificar fila.

## D4 — Armazenamento de arquivos/documentos — ✅ Decidido: (B) MinIO

**Opções:**
- (A) Volume local em disco (via Docker volume).
- (B) MinIO (S3-compatible, self-hosted via Docker).

| | (A) Volume local | (B) MinIO |
|---|---|---|
| Vantagens | Mais simples de configurar no início | API S3-compatible; troca para AWS S3 depois é quase transparente; ensina o padrão usado em produção |
| Desvantagens | Acoplamento a filesystem local dificulta a evolução para cloud depois | Mais um serviço no docker-compose |
| Custo | Zero | Zero (self-hosted) |
| Impacto no aprendizado | Baixo | Médio (padrão de storage de objetos, relevante para AWS depois) |

**Recomendação:** (B) MinIO. Baixo custo de complexidade adicional (só mais um container) e alinhado ao princípio de preparar a evolução futura para AWS sem depender dela agora.

## D5 — Papéis de LangChain, LangGraph e LlamaIndex — ✅ Decidido: (B) Papéis distintos e sequenciais

**Opções:**
- (A) Usar os três já misturados desde o início na construção do RAG e do agente.
- (B) Papéis distintos e sequenciais: LangChain para loaders/text-splitters; LangGraph para orquestração do agente; RAG construído "na mão" contra o pgvector primeiro, com LlamaIndex avaliado depois como exercício comparativo.

| | (A) Tudo misturado | (B) Papéis distintos e sequenciais |
|---|---|---|
| Vantagens | Menos decisões de fronteira entre bibliotecas | Cada biblioteca é estudada isoladamente, no seu ponto forte; entender o RAG "por baixo dos panos" antes de usar um framework que abstrai isso |
| Desvantagens | Risco de aprender 3 frameworks sobrepostos ao mesmo tempo sem entender o que cada um resolve | Mais uma etapa (reconstruir/comparar com LlamaIndex depois) |
| Custo | Zero | Zero |
| Impacto no aprendizado | Médio, mas raso (confunde responsabilidades) | Alto — o objetivo explícito do projeto é estudar as três tecnologias, e fica mais claro o que cada uma contribui |

**Recomendação:** (B). Construir o RAG manualmente com pgvector primeiro (Fase 7) ensina os fundamentos (chunking, embeddings, busca, prompt com contexto); LlamaIndex entra depois como comparação explícita ("o que esse framework me economiza?").

## D6 — Modelo de embeddings — ✅ Decidido (provisoriamente): (A) Ollama `nomic-embed-text`

**Opções:**
- (A) Modelo de embedding servido via Ollama (ex.: `nomic-embed-text`).
- (B) `sentence-transformers` (Hugging Face), rodando localmente em Python.

| | (A) Ollama | (B) sentence-transformers |
|---|---|---|
| Vantagens | Um único runtime (Ollama) para LLM e embeddings | Ecossistema grande de modelos, incluindo opções multilíngues fortes em PT-BR |
| Desvantagens | Menos opções de modelo especificamente otimizado para PT-BR | Mais uma dependência/runtime além do Ollama |
| Custo | Zero | Zero |
| Impacto no aprendizado | Médio | Médio |

**Decidido:** `nomic-embed-text` via Ollama (768 dimensões), escolhido para desbloquear a implementação de FASE7-IMPL-01 (SCRUM-88) antes do estudo empírico formal (FASE7-EST-01) ter sido de fato executado — a comparação com `sentence-transformers` planejada nesse estudo continua valendo como validação posterior; se o resultado apontar `sentence-transformers` como melhor em PT-BR, revisitar esta decisão implica nova migration para `document_chunks.embedding` (a dimensão do vetor está fixada na coluna, ver `20260927130000_create_document_chunks_and_indexacao_status.py`).

## D7 — Observabilidade e avaliação de IA — ✅ Decidido: (B) Ragas/promptfoo

**Opções:**
- (A) Construir avaliação própria do zero (scripts customizados).
- (B) Usar ferramenta open source de avaliação (ex.: Ragas para RAG, promptfoo para comparação de prompts/modelos).

| | (A) Própria | (B) Ragas/promptfoo |
|---|---|---|
| Vantagens | Controle total, zero dependência externa | Métricas padronizadas (faithfulness, relevância) já implementadas, usadas no mercado |
| Desvantagens | Reinventa a roda, mais fácil de "parecer que funciona" sem métrica real | Curva de aprendizado da ferramenta |
| Custo | Zero | Zero (open source) |
| Impacto no aprendizado | Baixo (não ensina o estado da arte de avaliação) | Alto (ferramentas realmente usadas em produção) |

**Recomendação:** (B). Usar Ragas para avaliação de RAG e promptfoo (ou equivalente) para comparação de prompts/modelos; logging estruturado próprio (latência, tokens, custo) continua sendo construído manualmente, pois é simples e específico do domínio.

**Implementação (SCRUM-113/FASE10-IMPL-03, SCRUM-114/FASE10-IMPL-04) — adaptação necessária:** a lib `ragas` **não foi instalada no backend** — `pip install --dry-run ragas` mostrou que ela força upgrade de `langgraph` (0.2.60 → 1.2.x) e `langchain-text-splitters`, breaking change que quebraria `app.ai_agents` (API de `StateGraph`/`MemorySaver` mudou entre essas versões) e `app.ai_rag.infrastructure.chunking`. Em vez disso, `backend/eval/faithfulness.py` implementa a métrica de faithfulness do jeito que o Ragas faz (LLM-as-juiz, prompt pedindo um score 0–1 justificado) sem a dependência pesada — validado empiricamente: uma regressão proposital no prompt do RAG (instrução para "inventar" quando faltar contexto) derrubou o faithfulness médio de ~1.0 para 0.16 numa corrida real (ver handoff de SCRUM-114). `promptfoo` continua usável como está — é um CLI Node, roda fora do processo/venv Python, sem esse conflito (`backend/eval/promptfooconfig.yaml`). Reavaliar `ragas` de verdade se o avaliador for isolado num venv/processo próprio, separado da API.

## D8 — Biblioteca de mapa multiplataforma (native + web) — ✅ Revisada: MapLibre nas duas plataformas (ver D10)

Consequência direta de D2 (Expo for Web): `react-native-maps`, cogitado inicialmente para o mobile, não tem implementação web própria. A versão original desta decisão (wrapper comunitário do `react-native-maps` sobre a API JS do Google Maps, com Leaflet como plano B) foi **substituída** pela D10, porque o Google Maps Platform exige conta de faturamento (cartão) mesmo dentro do free tier.

**Resultado:** o mapa é isolado em `LoteamentoMap` (props: lista de polígonos + callback de seleção). O nativo usa `@maplibre/maplibre-react-native`; a Fase 5 adiciona `LoteamentoMap.web.tsx` com `maplibre-gl` (mesmo motor e mesmo estilo de mapa), sem wrapper comunitário do `react-native-maps`. A interface de props continua idêntica nas duas plataformas.

## D10 — Provedor de mapa: MapLibre + tiles do OpenStreetMap (sem Google Maps) — ✅ Decidido

Motivação: a chave do Google Maps (SCRUM-70) exigia conta de faturamento com cartão de crédito; o projeto é de portfólio/aprendizado e deve rodar sem custo nem cadastro pago.

**Opções:**
- (A) Google Maps Platform (`react-native-maps` + API JS na web).
- (B) MapLibre (open source) com tiles raster do OpenStreetMap — **escolhida**.
- (C) Mapbox (SDK próprio, exige token e tem free tier condicionado a conta).

| | (A) Google Maps | (B) MapLibre + OSM | (C) Mapbox |
|---|---|---|---|
| Custo / cadastro | Exige faturamento (cartão) | Zero, sem conta nem chave | Token + conta |
| Nativo + web | `react-native-maps` + wrapper web instável | `@maplibre/maplibre-react-native` + `maplibre-gl` (mesmo motor) | SDK equivalente |
| Expo Go | Não renderiza (chave embutida rejeitada) | Não (módulo nativo) — exige development build | Não |
| Vantagens | Imagens de satélite de alta qualidade | Open source, sem lock-in, estilo trocável por URL | Bom visual |
| Desvantagens | Custo/cartão; wrapper web menos maduro | Tiles públicos do OSM têm política de uso justo (ok para dev/demo) | Conta + token |

**Consequências:**
- Estilo do mapa é um objeto/URL de estilo; trocar de provedor de tiles (MapTiler, Stadia, tiles próprios em produção/Fase 11) é mudar uma constante. Uso em produção com tráfego real exige um provedor de tiles próprio ou pago — os tiles `tile.openstreetmap.org` são só para desenvolvimento/demonstração e exigem atribuição "© OpenStreetMap contributors" (exibida pelo componente).
- PostGIS continua sendo a fonte de verdade geográfica; o mapa é só visualização.
- Requer **development build** (`expo prebuild` + `expo run:android`); Expo Go não serve mais para a tela de mapa (não serve nem com Google, ver guia).

**Atualização (SCRUM-100, FASE8-IMPL-02):** camada de satélite adicionada como toggle — `Esri World Imagery` (`server.arcgisonline.com/.../World_Imagery`), serviço público gratuito, sem conta nem chave (mesmo padrão de uso do OSM, ver `mobile/src/lib/mapStyle.ts`). Motivado por precisar conferir visualmente se um polígono sugerido pela IA (extração de imagem) cai sobre o lote/casa certo — mapa só de ruas não mostra construções. Hoje só na versão web (`LoteamentoMap.web.tsx`, `PoligonoEditorMapa.web.tsx`), via botão que alterna a visibilidade da camada (não troca o `style` inteiro, pra não derrubar overlays desenhados por cima); nativo (`LoteamentoMap.tsx`) importa o mesmo style compartilhado mas ainda sem o toggle — nenhuma tela nativa hoje precisa dele.

## D9 — Biblioteca de componentes multiplataforma (mobile + web) — ✅ Decidido: (A) React Native Paper

Decisão motivada pelo comentário em SCRUM-63 pedindo para definir o design da aplicação junto com o setup do Expo (FASE3-IMPL-01) — esse padrão vale para as telas de domínio da Fase 3 e para o backoffice web da Fase 5 (D2). Pesquisa de apoio (apps do nicho, CRMs de loteamento, SaaS backoffice) em [docs/design/referencias-apps.md](design/referencias-apps.md); opções comparadas em [docs/design/proposta-design-system.md](design/proposta-design-system.md).

**Opções:**
- (A) React Native Paper (Material Design 3, mantida pela Callstack) — **escolhida**.
- (B) Tamagui (tokens + compilador, pensado para nativo+web desde a raiz).
- (C) Componentes próprios sobre `View`/`Pressable`/`Text`, sem biblioteca.

| | (A) React Native Paper | (B) Tamagui | (C) Componentes próprios |
|---|---|---|---|
| Vantagens | Setup rápido; acessibilidade (alvos de toque, screen reader) já resolvida; madura desde 2017 | Melhor caso de uso para web como alvo de primeira classe; tokens nativos | Controle total; zero dependência |
| Desvantagens | Web via RN Web é suportada mas não é o caso de uso mais testado da lib | Setup mais pesado (config + compilador); curva de aprendizado maior | Reinventa botão, input, modal — atrasa a Fase 3 sem ganho de aprendizado central para o projeto |
| Custo | Zero | Zero | Zero |
| Impacto no aprendizado | Médio | Médio-alto (concentrado em ferramenta, não em domínio) | Baixo |

**Recomendação:** (A). Foco do projeto é domínio + IA, não profundidade em design system — Paper resolve componentes básicos (lista, botão, badge, input) rápido e com acessibilidade de graça. Reavaliar para (B) Tamagui só se a Fase 5 (Expo for Web) expuser limitação real de estilização compartilhada — mesmo critério usado em D8 para o wrapper de mapa.

**Identidade visual (cor/tipografia/componentes):** gerada no [Lovable](https://github.com/talles-coder/lotiado-gest-o-imobili-ria-inteligente) a partir de um brief próprio ([docs/design/lovable-brief.md](design/lovable-brief.md)) e mapeada em detalhe em [docs/design/lovable-mapeamento.md](design/lovable-mapeamento.md) — **fonte de verdade dos tokens** (cores em hex, tipografia Outfit/Figtree, raio, sombra, componentes como `Logo`/`StatusBadge`, padrões de tela). Regra permanente: qualquer trabalho de estilo/UI segue esse mapeamento, não inventa token novo fora dele.

## Registro de decisões tomadas durante a execução

Conforme as fases avançarem e decisões como D6 forem resolvidas empiricamente, o resultado deve ser adicionado como uma nova entrada neste documento (ex. "D6 — decidido: Ollama nomic-embed-text, ver task FASE7-EST-03").

### Auditoria (FASE1-IMPL-04) — decidido: rastreamento declarativo automático, não helper manual

A descrição original da task previa um helper (`registrar_auditoria(...)`) chamado manualmente pelos services ao final de cada ação sensível. Trocado por rastreamento automático: `app.audit.infrastructure.tracking.rastrear_auditoria(...)` é um decorator aplicado **uma única vez** em cima do model (ex.: futuramente `Lote`, `ReservaVenda`), mapeando quais colunas são sensíveis para qual `AcaoAuditoria`. Um listener de `before_flush` do SQLAlchemy, registrado globalmente (importado em `app.database`), gera a entrada de `audit_log` sozinho sempre que um campo rastreado muda ou uma entidade marcada com `acao_criacao` é criada — nenhum service ou rota chama nada. Quem está autenticado na request chega até o listener via `contextvars`, populados pelo `AuditContextMiddleware` (registrado uma vez em `app.main`, não por rota). Se mais de um campo sensível mudar no mesmo flush e resolver para a mesma ação, vira uma única entrada com payload combinando os campos — nunca uma linha por campo.

**Por quê:** o objetivo é auditoria que não dependa de nenhum dev lembrar de chamar algo — um `git grep` por chamadas de auditoria nunca deveria ser necessário para saber se uma ação sensível está coberta. Não existe (deliberadamente) uma via de escape manual: hoje toda ação sensível listada na task (transição de status, criação/cancelamento de reserva, venda, alteração de preço, alteração de responsável) é expressável como "um ou mais campos de um model mudaram"; um helper manual paralelo seria código sem uso real. Se isso deixar de ser verdade (ex.: precisar registrar um motivo digitado pelo usuário, que não é uma coluna), a via de escape deve ser adicionada então — não antes.

**Impacto para o Dev 1 (FASE1-IMPL-01/03):** ao criar `Lote` e `ReservaVenda`, decorar com `@rastrear_auditoria(entidade=..., acao_criacao=..., campos_sensiveis={...})` em vez de chamar uma função ao final do service. Ver exemplos em `app/audit/infrastructure/tracking.py` e `backend/tests/test_audit_tracking.py`.

## D11 — Provedor de pagamento/boleto — ✅ Decidido: (A) Asaas

**Opções:**
- (A) Asaas — **escolhida**.
- (B) Iugu.
- (C) Gerencianet/Efí.
- (D) Pagar.me.

Todas oferecem boleto/PIX via API com free tier ou custo baixo por transação, suficiente para demonstração. **Decidido pelo critério combinado (2026-09-27): "escolher a de maior qualidade entre as que dão pra testar em sandbox sem gastar"** — Asaas tem sandbox gratuito sem exigir CNPJ ativo, documentação de API considerada a mais direta do grupo, e é a opção mais usada por SaaS/startups brasileiras nesse porte (mais exemplos/comunidade para apoiar o aprendizado). Abstraída atrás de um `PaymentProvider`, no mesmo padrão de `LLMProvider` (D1 em `01-analise-requisitos.md`) e da abstração de storage (D4) — trocar de provedor não deve exigir mudar lógica de negócio.

## D12 — Provedor de assinatura eletrônica — ✅ Decidido: (C) Autentique

**Opções:**
- (A) Clicksign.
- (B) D4Sign.
- (C) Autentique — **escolhida**.

**Decidido pelo mesmo critério de D11 (2026-09-27)**: Autentique tem um nível gratuito de verdade (não só trial por tempo limitado) suficiente para o volume de demonstração do portfólio, com API bem documentada — evita a necessidade de contrato comercial só para exercitar a Fase 13. Integração via API do provedor, não implementação própria de assinatura com validade jurídica (ICP-Brasil) — fora de escopo de portfólio.

## D13 — Biblioteca de i18n para o app Expo — ✅ Decidido: (A) `i18next` + `react-i18next`

**Opções:**
- (A) `i18next` + `react-i18next` (padrão de mercado, funciona em RN e web) — **escolhida**.
- (B) `expo-localization` + solução própria simples de dicionário de strings.

**Decidido (2026-09-27)**: mais robusto (pluralização, interpolação, fallback de idioma) e evita reinventar isso na mão quando mais telas/campos forem adicionados (Fase 22 já aumenta bastante o volume de texto). A Fase 18 (`FASE18-EST-01`) continua existindo como estudo de como configurar `i18next` especificamente no Expo, não mais como comparação entre opções.

## D14 — Estratégia de versionamento de API — ✅ Decidido: (B) Versionamento por header

**Opções:**
- (A) Versionamento por path (`/v1/...`, `/v2/...`).
- (B) Versionamento por header (`Accept: application/vnd.lotiado.v2+json`) — **escolhida**.

**Decidido (2026-09-27)**: mesmo sendo mais disciplinado de testar/documentar do que o path, é a abordagem que o usuário preferiu. A Fase 19 (`FASE19-IMPL-01/02`) muda de "criar `/v1/`, `/v2/` como prefixo de rota" para "o mesmo conjunto de rotas responde formatos diferentes conforme o header `Accept`", usando `Depends` do FastAPI para resolver a versão a partir do header e despachar para o serializador correto — a lógica de negócio (service) continua única, só a camada de interface (schema de resposta) varia por versão.

## D15 — Biblioteca de gráficos multiplataforma (native + web) — 🔓 Em aberto (deliberadamente — resolução por teste prático)

Mesmo dilema de D8/D9 (nativo + Expo for Web no mesmo código): a maioria das libs de gráfico React Native não tem suporte web maduro.

**Opções:**
- (A) `victory-native` (nativo) + `victory` (web) — mesma API declarativa, pacotes irmãos.
- (B) `react-native-gifted-charts` (nativo) com fallback próprio simples em SVG para web.
- (C) Componente de gráfico próprio em SVG (`react-native-svg`, já eventualmente presente via mapa) para os poucos tipos de gráfico necessários (linha de vendas, barra de sazonalidade).

**Critério de decisão confirmado (2026-09-27)**: nada de escolher por trade-off teórico — `FASE16-EST-01` implementa o **mesmo gráfico de teste nas três opções**, nas duas plataformas (native + web), e a escolha final é por resultado prático: menos erro/limitação encontrada durante a implementação e melhor resultado visual. Sem empate técnico previsto — o exercício decide, não uma tabela de vantagens.

## D17 — Biblioteca de validação de formulário no mobile — ✅ Decidido: (A) `Zod` + `react-hook-form`

Levantamento de código (2026-09-27) confirmou: hoje não existe Zod/Yup/nenhuma lib de validação no mobile — cada tela faz só `campo.trim() !== ''` manualmente (`mobile/app/clientes/novo.tsx`, `mobile/app/corretores/novo.tsx`).

**Opções:**
- (A) `Zod` + `react-hook-form` (schema declarativo, integra bem com TypeScript) — **escolhida**.
- (B) `Yup` + `react-hook-form` (alternativa mais antiga, API similar).
- (C) Continuar sem lib, só funções de validação próprias por campo (CPF, CRECI, telefone, etc.) chamadas manualmente.

**Decidido (2026-09-27)**: Zod centraliza a regra de validação num schema só, reaproveitável entre criar/editar, e escala bem com o número de campos novos da Fase 22. `FASE22-EST-01` continua existindo como estudo de como aplicar Zod especificamente aos formulários já existentes, não mais como comparação entre opções.

## D16 — Framework de teste E2E do mobile — ✅ Decidido: (B) Maestro, com fallback para (A) Detox

**Opções:**
- (A) Detox (E2E nativo, roda no device/emulador real, mantido pela Wix) — fallback.
- (B) Maestro (E2E declarativo em YAML, mais simples de escrever, CLI própria) — **escolhida como padrão**.
- (C) Playwright só para a versão web (Expo for Web) + teste manual guiado no nativo.

**Decidido (2026-09-27)**: Maestro é o ponto de partida por ser mais rápido de configurar (sem build nativo dedicado); `FASE23-EST-02` valida se ele atende o fluxo crítico da Fase 23 (login → criar cliente → criar reserva) — se alguma limitação real aparecer (ex.: interação que o Maestro não consegue automatizar de forma confiável), a fase cai para Detox em vez de forçar o Maestro a resolver algo fora do seu ponto forte.

## D18 — Biblioteca de animação/partículas para microinterações — ✅ Decidido: (A) `react-native-reanimated`

**Opções:**
- (A) `react-native-reanimated` (animação declarativa na UI thread).
- (B) Lottie (`lottie-react-native`, animação vetorial exportada do After Effects/Bodymovin).
- (C) `react-native-skia` (motor de desenho 2D, mais flexível pra partícula customizada, curva de aprendizado maior).

**Decidido (2026-09-28), fechamento empírico simplificado**: o critério original (`FASE26-EST-01`) previa testar as 3 nas duas plataformas antes de decidir. Na prática de `FASE26-IMPL-01`, optou-se por pular o comparativo formal de 6 execuções e ir direto com (A) `react-native-reanimated` — decisão confirmada pelo usuário (2026-09-28) — pelos seguintes motivos objetivos: já roda sobre Expo for Web sem shim adicional (mesma API em mobile/web, sem duplicar variação de animação por plataforma como aconteceria com Skia); não depende de asset externo exportado de outra ferramenta (Lottie exigiria criar/exportar arquivos `.json` do After Effects/Bodymovin, fora do escopo de protótipo rápido); e as variações propostas em `FASE26-IMPL-01` (paralaxe, partículas, pulse/lote itinerante, entrada "montada" do logo) são todas alcançáveis com transforms/opacity declarativos, sem precisar do motor de desenho customizado que justificaria Skia. `FASE26-EST-01` fica sem ticket próprio — se uma necessidade real de partícula complexa (ex. centenas de partículas físicas) aparecer depois, o comparativo formal com Skia pode ser revisitado então.

### D4 revisitada — imagem de MinIO gated: troca por `adobe/s3mock` (2026-09-28)

`quay.io/minio/minio` e `minio/minio` (Docker Hub) passaram a exigir login para pull anônimo — a decisão original em D4 (MinIO real via Docker) continua válida (S3-compatible, self-hosted), mas a imagem oficial não é mais publicamente puxável, quebrando CI e `docker compose up` num clone novo (só continuava funcionando em máquinas com a imagem já cacheada de antes do gating).

**Decidido:** trocar a imagem do serviço `minio` no `docker-compose.yml`/CI de `quay.io/minio/minio` para [`adobe/s3mock`](https://github.com/adobe/S3Mock) (API S3 compatível, ainda pública) — sem mudança de código de aplicação além de um detalhe de compatibilidade (ver abaixo). Efeitos:
- Porta interna do container é fixa em `9090` (não configurável) — `MINIO_API_PORT` default mudou de `9000` para `9090` em `docker-compose.yml`/`.env.example`, e `minio_endpoint_url` default em `backend/app/config.py` acompanhou.
- s3mock não tem console web (era `:9001` no MinIO real) nem exige autenticação — `infra/minio/init/create-bucket.sh` trocou de `mc mb` (precisa de credenciais) para um `curl -X PUT` simples no path do bucket.
- **Achado durante a troca:** contra s3mock rodando atrás do port-forward do Docker Desktop no Windows, `boto3`/`botocore` trava com `ConnectionClosedError` em todo `put_object` — o cliente manda o header `Expect: 100-continue` mas não espera a resposta antes de já mandar o corpo, e o NAT do Docker Desktop derruba a conexão nesse meio-tempo (validado via socket raw: com o handshake pausado manualmente, a mesma requisição funciona). Fix em `backend/app/documentos/infrastructure/storage.py` (`_criar_client`): remove o header `Expect` via `client.meta.events.register("before-send.s3.*", ...)` antes de mandar qualquer request — inofensivo contra qualquer S3 real, só desativa uma otimização opcional do protocolo. Sem esse fix, upload de documento quebra em dev local no Windows (CI em Linux não reproduz, mas o fix cobre os dois).

### Nomenclatura de migrations Alembic — decidido: revision ID com timestamp

A primeira migration (FASE0-IMPL-04) usava numeração sequencial manual (`001_create_tenants_table.py`). Com dois devs criando migrations em branches paralelas, numeração sequencial colide facilmente (dois devs criam `002` ao mesmo tempo em branches diferentes).

**Decidido:** revision ID no formato `YYYYMMDDHHMMSS` (ex. `20260911100000`), gerado a partir do momento de criação da migration. Como o `file_template` padrão do Alembic é `%(rev)s_%(slug)s`, o nome do arquivo já nasce ordenável cronologicamente sem precisar mexer em `alembic.ini`. Timestamps são praticamente únicos entre devs, eliminando o ponto de conflito.
