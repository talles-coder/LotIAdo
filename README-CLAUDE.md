# Como Usar Claude Code com o Projeto Hope

Este documento explica como usar Claude Code de forma eficiente neste projeto, aproveitando as Skills configuradas e a estrutura de contexto preparada.

## TL;DR — Comandos Principais

```bash
# Preparar um commit
/commit

# Criar uma Pull Request com revisão automática
/create-pr

# Carregar Skills specificamente (automático na maioria dos casos)
# Python/FastAPI — automático ao editar .py
# Testes — automático ao editar testes
```

---

## Visão Geral do Projeto

**Hope** é um sistema SaaS multitenant para gestão imobiliária:
- **Backend:** FastAPI (Python), monólito modular
- **Frontend:** Expo (React Native) + web (Expo for Web)
- **Banco:** PostgreSQL + PostGIS + pgvector
- **IA:** RAG + agentes LangGraph (Fase 7+)
- **Infraestrutura:** Docker Compose (local), AWS (Fase 11+)

Projeto de portfólio com 11 fases incrementais. Você está na **Fase 0** (setup).

Documentação completa: `docs/` (leia quando precisar contexto)

---

## Arquitetura — O Essencial

```
Backend (FastAPI)
  ├── Módulos por domínio (tenancy, identity, loteamentos_lotes, ...)
  ├── Separação: domain/application/infrastructure/interface
  └── RLS no PostgreSQL (isolamento multi-tenant)

Frontend (Expo)
  ├── Um código-base, duas plataformas (mobile + web)
  └── Consome API REST do backend

Infraestrutura
  ├── Postgres + PostGIS + pgvector
  ├── Redis (fila a partir da Fase 7)
  ├── MinIO (armazenamento de arquivos)
  └── Ollama (LLM local)
```

Veja `docs/02-arquitetura.md` para diagramas.

---

## Como Começar com uma Task

Você recebeu uma tarefa do backlog (ex: "Implementar login"). Siga assim:

### 1. Ler a Task (30 segundos)

Arquivo: `docs/backlog/fase-0-fundamentos.md` (ou fase correspondente)

Procure pela task ID (ex: `FASE0-IMPL-05`). Leia:
- Objetivo
- Descrição
- Dependências e pré-requisitos
- Critérios de aceite

### 2. Ler Documentação Mínima (2-5 min)

A task menciona documentos? Leia **só** as seções referenciadas:

Exemplos:
- Task de login? → Leia `docs/01-analise-requisitos.md` (seção "Autenticação")
- Task de multi-tenancy? → Leia `docs/02-arquitetura.md` (seção "Multi-tenancy")

**Não leia `docs/` inteiro** — economiza tokens e mantém contexto enxuto.

### 3. Navegar Código Existente (1-2 min)

Se estendendo módulo já existente:
- Procure arquivo semelhante (ex: "vou criar endpoint de login, qual endpoint já existe?")
- Veja padrões já estabelecidos (estrutura de pastas, nomes, imports)
- Copie estrutura, não invente de novo

### 4. Implementar

Use as Skills apropriadas (carregam automaticamente):

**Python/FastAPI:** Ao editar `.py`, Skill `python-fastapi` sugere padrões
- Type hints obrigatórios
- Separação domain/application/interface
- Nomes descritivos
- Async/await

**Testes:** Ao editar testes, Skill `testing` sugere
- pytest + fixtures
- Isolamento de BD
- Setup/Act/Assert
- Async tests

### 5. Validar Localmente

```bash
# Testes
pytest tests/ -v

# Lint
ruff check .

# Type check
mypy app/

# Format
black app/
```

### 6. Commitar

Quando pronto:
```bash
/commit
```

Claude vai:
- Analisar mudanças
- Sugerir commits separados se houver responsabilidades distintas
- Propor mensagem Conventional Commit (feat, fix, test, docs, etc)
- Validar secrets, debug, etc
- Executar commit

### 7. Criar PR

Quando branch está pronta para review:
```bash
/create-pr
```

Claude vai:
- Revisar diff completo
- Verificar escopo (não implementou coisa extra?)
- Testar (pytest, lint, type check)
- Gerar descrição com template
- Validar "outro dev consegue entender sem histórico da conversa?"
- Criar PR via GitHub

---

## Skills — Referência Completa

### Automáticas (sem invocar)

| Skill | Quando | O que faz |
|---|---|---|
| `python-fastapi` | Ao editar `.py` | Type hints, separação domain/app/interface, async/await, nomes, exceptions |
| `testing` | Ao editar testes | pytest, fixtures, isolamento de BD, parametrização, mocks, async tests |

### Manuais (invocar com /)

| Comando | Quando | O que faz |
|---|---|---|
| `/commit` | Pronto para commitar | Valida mudanças, propõe Conventional Commit, executa commit |
| `/create-pr` | Branch pronta para review | Revisa escopo, roda testes, gera PR com handoff completo |

---

## Conventional Commits — Formato

Usado pelo `/commit`:

```
<type>(<scope>): <subject>
```

**Types:**
- `feat` — Nova funcionalidade
- `fix` — Correção de bug
- `test` — Novo teste
- `docs` — Documentação
- `refactor` — Mudança sem alterar comportamento
- `chore` — Setup, deps, config
- `perf` — Performance
- `ci` — CI/CD

**Exemplos:**
- `feat(auth): add JWT token generation`
- `fix(tenancy): ensure tenant_id filter in all queries`
- `test(reserva): add regression test for concurrent reservation`
- `docs(CLAUDE.md): update context navigation`

❌ Evitar: "fix stuff", "updates", "ajustes", "WIP"

---

## Estrutura de Pastas

```
hope/
├── docs/                       # Especificação do projeto
│   ├── 01-analise-requisitos.md
│   ├── 02-arquitetura.md
│   ├── 03-decisoes-tecnicas.md
│   ├── 04-roadmap.md
│   └── backlog/                # Tarefas por fase
│       ├── fase-0-fundamentos.md
│       ├── fase-1-mvp-dominio.md
│       └── ...
├── backend/                    # Backend FastAPI
│   ├── app/
│   │   ├── main.py            # Entrada, configuração
│   │   ├── config.py          # Settings via pydantic
│   │   └── modules/
│   │       ├── tenancy/       # Exemplo de módulo
│   │       │   ├── domain/
│   │       │   ├── application/
│   │       │   ├── infrastructure/
│   │       │   └── interface/
│   │       └── identity/      # Outro módulo
│   ├── tests/
│   ├── alembic/               # Migrations
│   ├── requirements.txt
│   └── pytest.ini
├── mobile/                     # Frontend Expo (React Native + Web)
│   ├── app.json               # Configuração Expo
│   ├── src/
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml         # Serviços: Postgres, Redis, Ollama, MinIO
├── .claude/                   # Configuração Claude Code
│   ├── skills/
│   │   ├── python-fastapi/
│   │   ├── testing/
│   │   ├── commit/
│   │   └── create-pr/
│   └── settings.json
├── CLAUDE.md                  # Este projeto + regras operacionais
├── README.md                  # Overview técnico
└── README-CLAUDE.md           # Este arquivo (como usar Claude)
```

---

## Fluxo de Trabalho Típico

### Cenário: Implementar Login (FASE0-IMPL-05)

```
1. Lê tarefa em docs/backlog/fase-0-fundamentos.md
   └─ Objetivo: "POST /auth/login retorna JWT"

2. Ler docs/01-analise-requisitos.md (seção D1 — autenticação)
   └─ Entender: JWT próprio + RBAC mínimo

3. Ver código de tenancy (já implementado em FASE0-IMPL-04)
   └─ Copiar padrão: domain/application/interface

4. Implementar:
   • models.py: User, UserTenantMembership
   • domain/: validar senha
   • application/: serviço de login
   • interface/: rota FastAPI POST /auth/login
   • tests/: teste de sucesso + erro

5. /commit
   └─ Mensagem: "feat(identity): add JWT login endpoint"

6. /create-pr
   └─ Descrição automática, checklist, pronto para review
```

### Cenário: Bug em Multi-tenancy

```
1. Task: "Validar isolamento de tenant em queries"
   └─ Arquivo: docs/backlog/fase-2-multi-tenancy.md

2. Ver docs/01-analise-requisitos.md (seção "RLS", risk D3)
   └─ Entender: sempre filtrar tenant, RLS é defesa em profundidade

3. Grep por queries de domínio
   └─ Achar: "SELECT * FROM lotes" sem WHERE tenant_id

4. Fix: adicionar WHERE clause

5. Teste de regressão: dois tenants não veem dados um do outro

6. /commit
   └─ "fix(geo): ensure tenant_id filter in spatial queries"

7. /create-pr
   └─ Explicar: risco, como testar
```

---

## Dicas de Eficiência

### Contexto Enxuto

✅ **Faça:**
- Leia a task first
- Identifique documentação necessária (seção específica, não arquivo inteiro)
- Procure padrões no código existente
- Expanda contexto só se surgir dependência nova

❌ **Evite:**
- Reler `docs/` em cada tarefa
- Abrir arquivos "por garantia"
- Reproduzir documentação no chat ("segundo o docs...")
- Carregar todo o projeto mentalmente

### Multi-tenancy

⚠️ **Regra de ouro:** Toda query de domínio filtra `tenant_id`.
- `SELECT * FROM tabela WHERE tenant_id = ...`
- Exceção: tabelas de sistema (tenants, users)

### Decisões Arquiteturais

Se algo em `docs/` precisar mudar (stack, arquitetura), **update `docs/` primeiro** no commit/PR. Não decide sozinho.

### Dois Desenvolvedores

Cada fase tem "Divisão de trabalho e sincronização" no backlog.
- Sincronizar em contratos (schema, endpoint format, env vars)
- Paralelizar quando possível
- Se algo é inesperado, investigue — pode ser trabalho recente do outro dev

---

## Exemplos de Comandos

### Implementando um endpoint

```bash
# Claude: explica padrões de FastAPI/domain/application
# (Skill automática ao editar .py)

# Você cria module/interface/routers.py, application/services.py, etc
```

### Escrevendo testes

```bash
# Claude: pytest, fixtures, Setup/Act/Assert, async
# (Skill automática ao editar tests)

# Você cria tests/test_login.py com fixtures e parametrização
```

### Pronto para commitar

```bash
/commit

# Claude analisa mudanças, sugere commits, executa
```

### Pronto para PR

```bash
/create-pr

# Claude revisa escopo, roda testes, gera descrição, cria PR
```

---

## Recuros Úteis

| Recurso | Onde | Por quê |
|---|---|---|
| **Análise de requisitos** | `docs/01-analise-requisitos.md` | Entender produto, decisões bloqueantes, riscos |
| **Arquitetura** | `docs/02-arquitetura.md` | Diagramas, fluxos, módulos |
| **Decisões técnicas** | `docs/03-decisoes-tecnicas.md` | Stack, opções, trade-offs |
| **Roadmap** | `docs/04-roadmap.md` | Fases, sequência, dependências |
| **Backlog detalhado** | `docs/backlog/fase-N-*.md` | Tasks, critérios de aceite, paralelização |
| **Regras operacionais** | `CLAUDE.md` | Multi-tenancy, contexto, skills |
| **Este documento** | `README-CLAUDE.md` | Como usar Claude aqui |

---

## Troubleshooting

**P: Contexto está muito grande, tokens consumindo rápido**
R: Você leu `docs/` inteiro? Leia só a seção referenciada pela task. Procure padrões no código antes de perguntar.

**P: Não sei qual é a próxima tarefa**
R: Veja `docs/backlog/fase-0-fundamentos.md` — está ordenada. Procure tasks com "Dependências: nenhuma" ou já concluídas.

**P: Outro dev fez mudança que não esperava**
R: Investigue! Pode ser trabalho paralelo recente. Veja `git log` e `git status`.

**P: Qual decisão arquitetural aplica aqui?**
R: Procure em `docs/03-decisoes-tecnicas.md`. Se não estiver, é abertura — registre em issue/PR.

**P: Como testar offline?**
R: Fase 6+. Agora é Fase 0 — sem offline ainda.

**P: Onde fica RLS no código?**
R: Fase 2. Agora é Fase 0 — sem RLS ainda. Prepare tabelas com `tenant_id`, RLS vem depois.

---

## Resumo — Use Assim

1. **Receba task** → leia em `docs/backlog/`
2. **Contexto mínimo** → seção específica de `docs/`, padrões no código
3. **Implemente** → Skills automáticas carregam padrões
4. **Valide** → `pytest`, lint, type check localmente
5. **`/commit`** → Conventional Commit automático
6. **`/create-pr`** → Revisão + handoff automático
7. **Outro dev faz code review** → merge, próxima task

**Filosofia:** Contexto enxuto + Skills automáticas + Documentação compartilhada = desenvolvimento eficiente entre múltiplos devs.

---

*Última atualização: 2026-09-11*
*Manter alinhado com `CLAUDE.md` e `docs/`*
