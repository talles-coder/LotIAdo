# Fase 0 — Fundamentos & Scaffolding

Ver formato das tasks em [README.md](README.md). Entrega desta fase: repositório funcional, todos os serviços de infraestrutura de base rodando via Docker Compose, skeleton do backend modular, módulos `tenancy`+`identity` mínimos (sem RLS ainda — isso é Fase 2), testes de setup passando.

## Épico E0.1 — Repositório e convenções

### FASE0-IMPL-01 — Inicializar repositório e estrutura de pastas
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** ter um repositório git com a estrutura de pastas do monólito modular pronta para receber código.
- **Descrição:** `git init`; estrutura `backend/`, `mobile/`, `backoffice/` (pode viver dentro de `backend/` como módulo de interface, decidir ao chegar na Fase 5), `docs/` (já existente); `.gitignore` para Python/Node; `README.md` raiz com visão geral e link para `docs/`.
- **Pré-requisitos:** nenhum.
- **Dependências:** nenhuma.
- **Resultado esperado:** repo inicial commitado.
- **Critérios de aceite:** `git log` mostra commit inicial; estrutura de pastas existe.
- **Paralelizável:** Não é necessário paralelizar — é o ponto de partida único do repo.
- **Conhecimentos novos introduzidos:** nenhum.

## Épico E0.2 — Docker Compose com serviços de base

### FASE0-EST-01-D1 / FASE0-EST-01-D2 — Estudo: Docker Compose multi-serviço
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como orquestrar múltiplos serviços com dependências (Postgres, Redis, Ollama, MinIO) via Docker Compose, incluindo healthchecks e volumes persistentes.
- **Conceitos a entender:** serviços/redes/volumes no Compose; `depends_on` com `condition: service_healthy`; variáveis de ambiente e `.env`; imagens oficiais com extensões (Postgres com PostGIS/pgvector).
- **Material recomendado:** documentação oficial do Docker Compose; imagem `postgis/postgis` (já inclui PostGIS); documentação do `pgvector` para habilitar a extensão via `CREATE EXTENSION`; documentação oficial do Ollama para rodar em container.
- **Exercício prático:** subir um `docker-compose.yml` de teste com dois serviços (ex.: Postgres + um serviço que espera o Postgres ficar saudável antes de iniciar) fora do projeto principal.
- **Critério de conclusão:** consegue explicar a diferença entre `depends_on` simples e com healthcheck, e escrever um compose de 2 serviços do zero.
- **Paralelizável:** Sim.

### FASE0-IMPL-02 — docker-compose.yml com Postgres+PostGIS+pgvector, Redis, Ollama, MinIO
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** todos os serviços de infraestrutura sobem com um único `docker compose up`.
- **Descrição:** usar imagem `postgis/postgis` (Postgres com PostGIS pré-instalado) e habilitar `pgvector` via script de init SQL (`CREATE EXTENSION IF NOT EXISTS postgis; CREATE EXTENSION IF NOT EXISTS vector;`); serviço Redis padrão; serviço Ollama com volume persistente para os modelos baixados; serviço MinIO com bucket inicial criado via script de init.
- **Pré-requisitos:** FASE0-EST-01-D2.
- **Dependências:** FASE0-IMPL-01.
- **Resultado esperado:** `docker compose up` sobe Postgres (com extensões ativas), Redis, Ollama, MinIO, todos saudáveis.
- **Critérios de aceite:** `docker compose ps` mostra todos os serviços "healthy"; `psql` consegue rodar `SELECT postgis_version();` e `SELECT * FROM pg_extension WHERE extname='vector';` com sucesso.
- **Paralelizável:** Sim, em paralelo com FASE0-IMPL-03 (skeleton do backend) — só precisam sincronizar na variável de ambiente de conexão (`DATABASE_URL`) antes do backend tentar conectar de fato.
- **Conhecimentos novos introduzidos:** Docker Compose multi-serviço, PostGIS/pgvector como extensões Postgres, MinIO.

## Épico E0.3 — Skeleton do backend modular

### FASE0-EST-02-D1 / FASE0-EST-02-D2 — Estudo: arquitetura modular em FastAPI (monólito)
- **Tipo:** Estudo
- **Dev:** Dev 1 e Dev 2
- **Objetivo:** entender como estruturar um monólito modular em Python/FastAPI com separação leve entre domain/application/infrastructure/interface, sem cair em over-engineering.
- **Conceitos a entender:** dependency injection do FastAPI (`Depends`); organização por módulo de domínio (vertical slices) vs. por camada técnica (horizontal layers); onde fica a fronteira entre "regra de negócio" e "acesso a dado"; SQLAlchemy async + `asyncpg`.
- **Material recomendado:** documentação oficial do FastAPI (seção de Bigger Applications / Dependencies); documentação do SQLAlchemy 2.0 (modo async).
- **Exercício prático:** criar um mini-módulo de exemplo (ex.: "notas") fora do domínio real do projeto, com uma rota, um serviço de aplicação e um repositório, para fixar o padrão antes de aplicá-lo ao domínio real.
- **Critério de conclusão:** consegue explicar por que o módulo é organizado por domínio (vertical) e não replicar isso incorretamente como camadas técnicas globais (`routes/`, `services/`, `models/` soltos na raiz).
- **Paralelizável:** Sim.

### FASE0-IMPL-03 — Skeleton FastAPI com módulos vazios e convenção de módulo
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** ter a convenção de módulo (domain/application/infrastructure/interface) estabelecida e replicável para os módulos futuros.
- **Descrição:** criar `backend/app/main.py`, configuração (`Settings` via `pydantic-settings`, lendo `.env`), conexão SQLAlchemy async, estrutura de pastas para os módulos futuros (`tenancy/`, `identity/`, `loteamentos_lotes/`, etc., cada um vazio ou com um exemplo mínimo), Alembic configurado para migrations.
- **Pré-requisitos:** FASE0-EST-02-D1.
- **Dependências:** FASE0-IMPL-01. Precisa de `DATABASE_URL` combinada com FASE0-IMPL-02 (ponto de sincronização).
- **Resultado esperado:** `uvicorn app.main:app` sobe e responde em `/health`.
- **Critérios de aceite:** endpoint `/health` retorna 200; `alembic upgrade head` roda sem erro (mesmo sem tabelas ainda, ou com uma tabela de exemplo).
- **Paralelizável:** Sim, com FASE0-IMPL-02 (ver ponto de sincronização acima).
- **Conhecimentos novos introduzidos:** estrutura modular do monólito, Alembic, SQLAlchemy async.

## Épico E0.4 — Módulos tenancy + identity mínimos

### FASE0-IMPL-04 — Módulo `tenancy`: modelo de Tenant e resolução por request
- **Tipo:** Implementação
- **Dev responsável:** Dev 2
- **Objetivo:** existir uma entidade `Tenant` e um mecanismo de resolver "qual tenant é esse request" — sem RLS ainda (isso é Fase 2), apenas o modelo de dados e a resolução.
- **Descrição:** tabela `tenants` (id, nome, slug, configurações básicas); toda tabela de domínio criada a partir de agora já nasce com coluna `tenant_id` (mesmo que a política RLS só seja ativada na Fase 2) — decisão registrada em [01-analise-requisitos.md](../01-analise-requisitos.md).
- **Pré-requisitos:** FASE0-IMPL-03.
- **Dependências:** nenhuma além do skeleton.
- **Resultado esperado:** tabela `tenants` existe e pode ser criada via migration; convenção de `tenant_id` documentada para todos os módulos futuros.
- **Critérios de aceite:** migration cria `tenants`; teste automatizado cria um tenant de exemplo.
- **Paralelizável:** Sim, com FASE0-IMPL-05 (identity), desde que ambos concordem antes no nome da coluna (`tenant_id`, tipo UUID) — ponto de sincronização.
- **Conhecimentos novos introduzidos:** nenhum além do já coberto em FASE0-EST-02.

### FASE0-IMPL-05 — Módulo `identity`: User, autenticação JWT mínima, `user_tenant_membership`
- **Tipo:** Implementação
- **Dev responsável:** Dev 1
- **Objetivo:** login funcional com JWT e o modelo de dados já preparado para um usuário pertencer a mais de um tenant no futuro (decisão registrada em [01-analise-requisitos.md](../01-analise-requisitos.md)).
- **Descrição:** tabela `users` (independente de tenant); tabela `user_tenant_membership` (user_id, tenant_id, papel); endpoint de login que emite JWT contendo `user_id` e, por ora, o único `tenant_id` da membership (Fase 1 é single-tenant na prática); hash de senha (`passlib`/`argon2`).
- **Pré-requisitos:** FASE0-IMPL-03.
- **Dependências:** FASE0-IMPL-04 (precisa da tabela `tenants` existir para a FK de `user_tenant_membership`).
- **Resultado esperado:** `POST /auth/login` retorna JWT válido; `GET /auth/me` autenticado retorna o usuário e seu tenant.
- **Critérios de aceite:** teste de integração cobre login com sucesso, login com senha errada (401), acesso a `/auth/me` sem token (401).
- **Paralelizável:** Não pode ser concluída antes de FASE0-IMPL-04 existir (FK), mas o desenvolvimento do endpoint de login em si pode começar em paralelo usando um `tenant_id` mockado, integrando de fato assim que a tabela `tenants` estiver pronta.
- **Conhecimentos novos introduzidos:** JWT, hashing de senha, modelagem de associação usuário↔tenant.

### FASE0-IMPL-06 — Testes de setup automatizados (pytest + fixtures de banco)
- **Tipo:** Implementação
- **Dev responsável:** qualquer um (recomendado: quem terminar primeiro entre FASE0-IMPL-04/05)
- **Objetivo:** garantir que o ambiente de testes automatizados existe desde o início (princípio "não deixar testes para o final").
- **Descrição:** configurar `pytest` + `pytest-asyncio`, fixture de banco de testes (schema limpo por teste ou transação com rollback), fixture de cliente HTTP (`httpx.AsyncClient` contra a app FastAPI).
- **Pré-requisitos:** nenhum estudo novo (reaproveita FASE0-EST-02).
- **Dependências:** FASE0-IMPL-03.
- **Resultado esperado:** `pytest` roda e executa os testes de FASE0-IMPL-04/05.
- **Critérios de aceite:** suíte de testes roda em CI local (`pytest` no terminal) sem estado compartilhado entre testes.
- **Paralelizável:** Sim, pode ser feito por quem estiver livre primeiro.
- **Conhecimentos novos introduzidos:** fixtures assíncronas de teste com banco real.

## Divisão de trabalho e sincronização

- **Dev 1:** FASE0-EST-02 → FASE0-IMPL-03 (skeleton) → FASE0-IMPL-05 (identity).
- **Dev 2:** FASE0-EST-01 → FASE0-IMPL-02 (docker-compose) → FASE0-IMPL-04 (tenancy).
- **Pontos de sincronização:**
  1. Formato de `DATABASE_URL`/variáveis de ambiente combinado antes de FASE0-IMPL-03 tentar conectar (depende de FASE0-IMPL-02).
  2. Nome/tipo da coluna `tenant_id` (UUID) combinado antes de FASE0-IMPL-04 e FASE0-IMPL-05 avançarem em paralelo.
  3. FASE0-IMPL-05 depende da tabela `tenants` (FASE0-IMPL-04) existir para aplicar a migration final — pode ser desenvolvida em paralelo com um mock e integrada ao final.
- **FASE0-IMPL-01** é sequencial e bloqueia tudo (só precisa ser feita uma vez, rapidamente, por Dev 1).
