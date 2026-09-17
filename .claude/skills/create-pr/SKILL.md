---
name: create-pr
description: Revisar branch e criar Pull Request com handoff completo
type: manual
invoke: /create-pr
---

# /create-pr — Revisar e Criar Pull Request

Invoke com `/create-pr` quando a branch estiver pronta para code review. Esta Skill:

1. Identifica branch atual e branch base
2. Analisa commits e diff desde base
3. Localiza task correspondente no backlog (se houver)
4. Verifica documentação relacionada
5. **Valida escopo** — não inclui funcionalidades futuras
6. Faz revisão técnica antes de abrir PR
7. Cria PR com descrição, checklist e handoff claro

## Revisão Técnica — Procura por

- ✅ Bugs óbvios
- ✅ Regressões
- ✅ Race conditions (concorrência)
- ✅ Problemas async
- ✅ Vazamento de tenant (multi-tenancy)
- ✅ Quebra de decisões arquiteturais
- ✅ Código desnecessário (dead code)
- ✅ Overengineering
- ✅ Funcionalidade fora do escopo (anticipatory features)
- ✅ Tratamento incorreto de erros
- ✅ Testes ausentes
- ✅ Secrets em código
- ✅ Logs/debug temporários
- ✅ Mudanças não relacionadas

## Validações Automáticas

Tenta executar (se disponível):
- `pytest` — testes passam?
- `ruff check` — lint ok?
- `black --check` — formato ok?
- `mypy` / `pyright` — type check ok?

## Quando invocar

✅ Branch finalizada, testes rodando, pronta para review.

❌ Não use se ainda houver work-in-progress.

## Handoff para Outro Dev

**Pergunta crítica:** "Outro dev que NÃO tem acesso ao histórico desta conversa conseguiria entender a mudança?"

Validações:
- [ ] Título claro do PR explica o quê/por quê
- [ ] Descrição cobre: problema, solução, riscos
- [ ] Diff é compreensível sem conversa fora do PR
- [ ] Testes explicam comportamento esperado
- [ ] Commit messages são descritivas
- [ ] Documentação atualizada (se necessário)

Se falhar nisso → PR não é criado. Claude sugere melhorias primeiro.

## Exemplo de Workflow

```bash
# ... você desenvolveu e testou localmente ...
$ /create-pr

# Claude analisa e sugere (ex):
# "PR revisor veria que você adicionou validação de CPF,
#  mas a documentação em docs/ não menciona essa regra.
#  Quer atualizar docs/ antes de abrir PR? (S/n)"

# Você ajusta. Depois Claude cria PR com gh.
```

## Branch por Task — OBRIGATÓRIO

⚠️ **Cada task = branch nova, NUNCA reutilize branches de outras tasks**

⚠️ **Sempre dar pull/fetch da `master` antes de criar a branch e começar a desenvolver** — `git fetch origin master` + branch criada a partir de `origin/master` (não de uma `master` local desatualizada). Outro dev pode ter mergeado algo enquanto a task estava sendo planejada; começar de uma base velha gera conflito maior depois e risco de reimplementar algo que já mudou (ex.: contrato de endpoint, schema). Se a branch já foi criada e a `master` andou nesse meio tempo, faça `git merge origin/master` antes de abrir o PR (não rebase — merge preserva o histórico de quem trabalhou em paralelo).

Padrão de nome:
```
feat/SCRUM-XX-descrição-curta
fix/SCRUM-XX-descrição-curta
chore/SCRUM-XX-descrição-curta
```

Exemplos:
- `feat/SCRUM-45-backend-skeleton`
- `feat/SCRUM-50-tenancy-module`
- `fix/SCRUM-48-tenant-isolation`

## Screenshots de Telas Novas — OBRIGATÓRIO

⚠️ **Toda tela nova ou alterada (mobile ou backoffice web) entra no PR com print.**

Antes de abrir o PR: suba a tela (`expo start --web` é suficiente pra captura, mesmo que o alvo real da task seja nativo — só documentar visualmente) e tire um screenshot de cada tela nova/alterada. Salve em `docs/design/screenshots/<task>-<tela>.png`, commite junto com o resto da task, e referencie as imagens na seção **Evidências** do PR (via raw.githubusercontent.com, apontando pra branch da PR — GitHub renderiza inline). PR com tela nova e sem print não está pronto para abrir.

## Formato do PR

**Idioma:** A descrição do PR (body) é **sempre em pt-BR**, mesmo que título, nomes de código, tipos de Conventional Commits e trechos de código permaneçam em inglês. Nunca gere o body em inglês.

**Título:** Deve começar com número da task
```
SCRUM-45: feat(backend): create FastAPI skeleton
SCRUM-50: feat(tenancy): implement multi-tenant isolation
```

**Corpo do PR:** use `.claude/skills/create-pr/template.md` como base **literal** — copie a estrutura de seções do arquivo e preencha cada uma (não parafraseie/resuma livremente em outro formato). Seções sem conteúdo relevante podem ser removidas (ver nota final do template), mas a ordem e os títulos das seções mantidas devem bater com o template:
- Resumo (problema, solução)
- Alterações principais
- Como testar
- Evidências (se houver)
- Riscos/impactos
- Checklist de handoff

## Após PR criado

- URL do PR exibida
- Nunca faz merge automaticamente
- Outro dev (ou CI) faz review

---

## Checklist — Antes de Chamar /create-pr

**Branch & Task:**
- [ ] Branch dedicada para esta task (nunca reutilize de outra task)
- [ ] Nome da branch segue padrão: `feat/SCRUM-XX-descrição` ou `fix/SCRUM-XX-descrição`
- [ ] Branch criada a partir da `master` **atualizada** (`git fetch origin master` antes de criar/começar; `git merge origin/master` se a `master` andou depois)
- [ ] Número da task está correto no nome da branch

**Código & Testes:**
- [ ] Testes passam localmente
- [ ] Lint/format/type check ok
- [ ] Nenhum commit WIP ou fixup pendente
- [ ] Escopo é exatamente o que a task pede (não mais)
- [ ] Documentação atualizada (se necessário)

**PR & Handoff:**
- [ ] Handoff é claro (outro dev sem contexto entende)
- [ ] Riscos/impactos mencionados (se houver)
- [ ] Título do PR começa com número da task (SCRUM-XX: ...)
- [ ] Tela nova ou alterada (mobile/web)? Screenshot tirado, commitado em `docs/design/screenshots/` e embutido na seção Evidências
