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

## Formato do PR

**Título:** Deve começar com número da task
```
SCRUM-45: feat(backend): create FastAPI skeleton
SCRUM-50: feat(tenancy): implement multi-tenant isolation
```

Segue template em `.claude/skills/create-pr/template.md`:
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
- [ ] Branch criada de `master` (não de outra feature branch)
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
