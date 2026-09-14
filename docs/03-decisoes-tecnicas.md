# 03 — Decisões Técnicas (Etapa 3)

Formato por decisão: opções, vantagens, desvantagens, custo, impacto no aprendizado, recomendação. As 4 decisões bloqueantes (backoffice web, isolamento multi-tenant, ambiente de IA, offline) já foram fechadas com o usuário e estão em [01-analise-requisitos.md](01-analise-requisitos.md) — não repetidas aqui. **D1–D7 abaixo já foram decididas com o usuário** (resultado marcado em cada uma); D6 fica deliberadamente em aberto até o estudo prático. D8 foi adicionada como consequência direta da decisão D2.

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

## D6 — Modelo de embeddings — 🔓 Em aberto (deliberadamente)

**Opções:**
- (A) Modelo de embedding servido via Ollama (ex.: `nomic-embed-text`).
- (B) `sentence-transformers` (Hugging Face), rodando localmente em Python.

| | (A) Ollama | (B) sentence-transformers |
|---|---|---|
| Vantagens | Um único runtime (Ollama) para LLM e embeddings | Ecossistema grande de modelos, incluindo opções multilíngues fortes em PT-BR |
| Desvantagens | Menos opções de modelo especificamente otimizado para PT-BR | Mais uma dependência/runtime além do Ollama |
| Custo | Zero | Zero |
| Impacto no aprendizado | Médio | Médio |

**Confirmado com o usuário:** decisão intencionalmente adiada para depois do estudo prático (FASE7-EST-01) — comparar empiricamente qualidade de recuperação em português nos dois, e só então registrar o resultado como uma decisão adicional neste documento (ex.: "D6 — decidido: Ollama nomic-embed-text").

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

## D8 — Biblioteca de mapa multiplataforma (native + web)

Nova decisão, consequência direta de D2 (Expo for Web): `react-native-maps`, usado no mobile desde a Fase 4, não tem implementação web própria.

**Opções:**
- (A) Wrapper comunitário que reimplementa a API do `react-native-maps` sobre a API JavaScript do Google Maps para o alvo web (ex.: `@teovilla/react-native-web-maps`), mantendo os mesmos componentes (`MapView`, `Polygon`) nas duas plataformas via arquivo `.web.tsx`.
- (B) Biblioteca de mapa própria da web (ex.: `react-leaflet`), sem tentar unificar a API com o mobile — cada plataforma com sua própria implementação de tela de mapa, sem componente compartilhado.

| | (A) Wrapper unificado (Google Maps) | (B) Biblioteca web própria (Leaflet) |
|---|---|---|
| Vantagens | Mesmo provider (Google Maps) e mesma API de componente nas duas plataformas; menos código de tela duplicado | Leaflet é open source, maduro, bem documentado; não depende da maturidade de um wrapper comunitário menor |
| Desvantagens | Wrapper comunitário é menos maduro/mantido que o `react-native-maps` oficial; ainda exige cuidado nas props não suportadas | Duas implementações de mapa (mobile e web) com APIs diferentes — tela de mapa não é 100% compartilhada, ainda que a lógica de negócio em volta seja |
| Custo | Zero (Google Maps JS API tem free tier generoso) | Zero |
| Impacto no aprendizado | Alto — reforça o padrão de abstração por plataforma já necessário para storage (D2) | Médio — aprende Leaflet, mas não aprofunda o padrão de abstração multiplataforma |

**Recomendação:** (A). Mantém consistência com a decisão de usar Google Maps como camada de visualização (briefing original) e reaproveita ao máximo o componente de mapa entre mobile e web — a tela de edição de polígono da Fase 5 adiciona só a camada de desenho por cima do mesmo `MapView` web. Se o wrapper comunitário se mostrar instável durante a Fase 5, cair para (B) como plano B, registrando a mudança aqui.

## Registro de decisões tomadas durante a execução

Conforme as fases avançarem e decisões como D6 forem resolvidas empiricamente, o resultado deve ser adicionado como uma nova entrada neste documento (ex. "D6 — decidido: Ollama nomic-embed-text, ver task FASE7-EST-03").

### Auditoria (FASE1-IMPL-04) — decidido: rastreamento declarativo automático, não helper manual

A descrição original da task previa um helper (`registrar_auditoria(...)`) chamado manualmente pelos services ao final de cada ação sensível. Trocado por rastreamento automático: `app.audit.infrastructure.tracking.rastrear_auditoria(...)` é um decorator aplicado **uma única vez** em cima do model (ex.: futuramente `Lote`, `ReservaVenda`), mapeando quais colunas são sensíveis para qual `AcaoAuditoria`. Um listener de `before_flush` do SQLAlchemy, registrado globalmente (importado em `app.database`), gera a entrada de `audit_log` sozinho sempre que um campo rastreado muda ou uma entidade marcada com `acao_criacao` é criada — nenhum service ou rota chama nada. Quem está autenticado na request chega até o listener via `contextvars`, populados pelo `AuditContextMiddleware` (registrado uma vez em `app.main`, não por rota). Se mais de um campo sensível mudar no mesmo flush e resolver para a mesma ação, vira uma única entrada com payload combinando os campos — nunca uma linha por campo.

**Por quê:** o objetivo é auditoria que não dependa de nenhum dev lembrar de chamar algo — um `git grep` por chamadas de auditoria nunca deveria ser necessário para saber se uma ação sensível está coberta. Não existe (deliberadamente) uma via de escape manual: hoje toda ação sensível listada na task (transição de status, criação/cancelamento de reserva, venda, alteração de preço, alteração de responsável) é expressável como "um ou mais campos de um model mudaram"; um helper manual paralelo seria código sem uso real. Se isso deixar de ser verdade (ex.: precisar registrar um motivo digitado pelo usuário, que não é uma coluna), a via de escape deve ser adicionada então — não antes.

**Impacto para o Dev 1 (FASE1-IMPL-01/03):** ao criar `Lote` e `ReservaVenda`, decorar com `@rastrear_auditoria(entidade=..., acao_criacao=..., campos_sensiveis={...})` em vez de chamar uma função ao final do service. Ver exemplos em `app/audit/infrastructure/tracking.py` e `backend/tests/test_audit_tracking.py`.

### Nomenclatura de migrations Alembic — decidido: revision ID com timestamp

A primeira migration (FASE0-IMPL-04) usava numeração sequencial manual (`001_create_tenants_table.py`). Com dois devs criando migrations em branches paralelas, numeração sequencial colide facilmente (dois devs criam `002` ao mesmo tempo em branches diferentes).

**Decidido:** revision ID no formato `YYYYMMDDHHMMSS` (ex. `20260911100000`), gerado a partir do momento de criação da migration. Como o `file_template` padrão do Alembic é `%(rev)s_%(slug)s`, o nome do arquivo já nasce ordenável cronologicamente sem precisar mexer em `alembic.ini`. Timestamps são praticamente únicos entre devs, eliminando o ponto de conflito.
