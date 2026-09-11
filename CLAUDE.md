# Claude Code — Contexto Operacional do Projeto

## Projeto

**Hope:** Sistema SaaS multitenant para gestão de loteamentos, imóveis e negociações imobiliárias. Monólito modular (FastAPI) + app Expo único (mobile + web backoffice) + PostgreSQL + IA (RAG + agentes LangGraph).

## Fonte da Verdade

- **`docs/`** — Especificação completa: análise de requisitos, arquitetura, decisões técnicas, roadmap, backlog detalhado por fase.
- **Não replique documentação** — Este arquivo é operacional, não substituto de `docs/`.

## Objetivo do Produto

Demonstrador de plataforma SaaS completa: da gestão de dados imobiliários (domínio + API) passando por mobile offline-capable, até IA com RAG e agentes autônomos. Projeto de portfólio + aprendizado (não visa produção no sentido de uptime/SLA).

## Escopo Fase 0 (MVP Inicial)

- Repositório + docker-compose com 4 serviços (Postgres+PostGIS+pgvector, Redis, Ollama, MinIO)
- Skeleton FastAPI com módulos vazios
- Módulos `tenancy` (multi-tenant) + `identity` (auth JWT) mínimos
- Testes e fixtures de banco
- **Fora do escopo:** Nenhuma implementação de negócio ainda; sem mobile; sem GIS; sem IA.

## Stack Definida

**Backend:**
- Python 3.11+, FastAPI, SQLAlchemy async, Alembic
- Postgres + PostGIS + pgvector (RLS por tenant)
- Redis (fila RQ a partir da Fase 7)
- MinIO (armazenamento de documentos/imagens)
- Ollama (LLM + embeddings locais)

**Frontend:**
- React Native + Expo (um único código-base)
- TypeScript
- Consome API REST JSON do backend

**Infrastructure:**
- Docker + Docker Compose (local)
- AWS (Fase 11, quando for cloud)

## Arquitetura — Decisões-Chave

1. **Monólito modular, não microservices** — Módulos por domínio (vertical slices), cada um com domain/application/infrastructure/interface.
2. **Um app Expo, duas plataformas** — Mobile + Web backoffice no mesmo código-base (Expo for Web / React Native Web), não dois frontends separados.
3. **Multi-tenancy via RLS** — Isolamento garantido no PostgreSQL, não apenas em camada de app.
4. **Offline somente-leitura** — Cache local no mobile; escrita exige internet (sem fila de sincronização no MVP).
5. **IA local** — Ollama com modelos pequenos (3B–8B), abstraído via `LLMProvider` para trocar de modelo/fornecedor.
6. **RLS + pool async** — Cuidado especial na Fase 2 com testes de isolamento (ver risk D3 em `03-decisoes-tecnicas.md`).

Ver `docs/02-arquitetura.md` para diagramas e fluxos completos.

## Regras Importantes

**Não quebre o escopo:**
- Não implemente funcionalidades de fases futuras antecipadamente apenas porque "seriam úteis".
- Use abstração quando surgir **problema concreto**, não porque "pode vir a ser necessário".
- Avoid overengineering: YAGNI é moto do projeto.

**Isolamento multi-tenant:**
- Toda tabela de domínio tem `tenant_id` (coluna + RLS quando Fase 2).
- Queries vetoriais (pgvector) incluem filtro de `tenant_id` explicitamente, como defesa em profundidade.
- Nunca `SELECT * FROM tabela` sem pensar em tenant — é risco de vazamento.

**Alterações de decisões registradas:**
- Se algo em `docs/` precisar mudar (arquitetura, decisão, stack), **update `docs/` primeiro**, depois comunique no backlog/PR.
- Decisões em aberto (ex: D6 — modelo de embeddings) ficam deliberadamente em aberto e ganham uma entry neste arquivo quando fechadas empiricamente.

## Backlog & Fases

Arquivo: `docs/backlog/` (um por fase: `fase-0-fundamentos.md`, `fase-1-mvp-dominio.md`, ..., `fase-11-cloud-producao.md`).

- **Fase 0–1:** Domínio + API (sem GIS, sem mobile).
- **Fase 2–3:** Multi-tenancy real + mobile MVP.
- **Fase 4–5:** GIS + backoffice web (Expo for Web).
- **Fase 6–8:** Offline cache + IA (RAG).
- **Fase 9–10:** Agentes LangGraph + observabilidade.
- **Fase 11:** Cloud/produção (AWS).

Cada phase é entrega funcional demonstrável.

## Navegação de Contexto por Tarefa

Ao receber uma tarefa (ex: "implementar login"):

1. **Localizar task no backlog** — Ex: `FASE0-IMPL-05` em `backlog/fase-0-fundamentos.md`.
2. **Ler só a task** — Objetivo, descrição, pré-requisitos, dependências, critérios de aceite.
3. **Ler documentação referenciada** — Se menciona `01-analise-requisitos.md` seção X, leia só essa seção.
4. **Ler código existente do módulo** — Se estendendo um módulo existente, procure patterns já estabelecidos.
5. **Expandir contexto se novo conceito** — Ex: "RLS não implementado antes"? Leia `docs/01-analise-requisitos.md` (risk D3) + a seção relevante de `02-arquitetura.md`.

**Princípio:** Context local first, breadth only when needed. Não carregue todo `docs/` automaticamente.

## Desenvolvimento & Commits

**Escopo focado:**
- Um commit = uma responsabilidade clara (feature / fix / test / doc).
- Use Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, etc.).
- Mensagem explícita: não "updates" ou "fixes stuff", mas "add login endpoint", "fix tenant isolation in audit log", etc.

**Antes de push:**
- Testes rodando localmente? ✅
- Lint/format? ✅
- Type checker (mypy/pyright)? ✅
- Nenhum `print()` ou `TODO` pendente? ✅
- Documentação atualizada se necessário? ✅

**Antes de PR:**
- Outra pessoa consegue entender a mudança lendo só a descrição do PR + diff, sem histórico da conversa com Claude? Sim? ✅
- Risk de conflito com outro dev trabalhando em paralelo? Sinalize na descrição.

## Trabalho em Equipe

**Dois desenvolvedores (Dev 1 + Dev 2):**
- Cada fase tem seção "Divisão de trabalho e sincronização" explicitando pontos de paralelização e bloqueios.
- **Pontos de sincronização** são contratos (schema, endpoint format, env var names) — devem ser acordados **antes** de codificar.
- Se encontrar algo diferente do esperado (arquivo novo, branch diferente), **investigue** — pode ser trabalho recente do outro dev.

**Evitar conflitos:**
- Não reorganize pastas ou refatore por "limpeza geral" junto com feature.
- Minimize quantidade de arquivos alterados.
- Não mude interfaces públicas (rotas de API, nomes de tabelas) sem coordenação.

## Decisões Abertas

- **D6 — Modelo de embeddings:** Ollama (`nomic-embed-text`) vs. `sentence-transformers`? Decidir empiricamente após FASE7-EST-01 (estudo prático de RAG), comparando qualidade em PT-BR.

## Continuidade de Conhecimento

**Règra de ouro:** O histórico de conversa com Claude **não é** fonte de verdade.

Se uma decisão, padrão ou requisito for necessário para outro dev (ou para você mesmo depois), deve estar em:
- `docs/` — decisões de arquitetura, requisitos, roadmap.
- Código — padrões consolidados, exemplos.
- Tests — comportamento esperado, edge cases.
- Commits + PR descriptions — mudanças recentes e seu motivo.
- `CLAUDE.md` (este arquivo) — regras transversais, navegação.

Nunca frases do tipo "como conversamos anteriormente" — registre no lugar apropriado.

## Como Usar as Skills

Disponível:
- `/commit` — Preparar commit com análise de escopo, sugestão de Conventional Commit.
- `/create-pr` — Revisar branch, criar PR com descrição, checklist, handoff para outro dev.
- `python-fastapi` (automática) — Padrões de Python/FastAPI quando editar código.
- `testing` (automática) — Boas práticas de pytest/testes quando criar testes.

Invocar as skills quando necessário — elas carregam automaticamente quando apropriado.

## Gerenciamento de Contexto e Tokens

**Economia de contexto = evitar contexto irrelevante, não ignorar dependências.**

Fluxo eficiente:
1. Task identificada → backlog localizado → documentação específica lida.
2. Código do módulo consultado para padrões existentes.
3. Contexto expandido somente se surgir dependência ou conceito novo.

**Evite:**
- Reler toda `docs/` em cada tarefa.
- Abrir arquivos "por garantia" sem relação à tarefa.
- Reproduzir documentação no chat — resuma, referencie `docs/`.

---

*Último update: 2026-09-11. Manter alinhado com `docs/` e reportar mudanças arquiteturais significativas.*
