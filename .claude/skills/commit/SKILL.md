---
name: commit
description: Preparar e validar commits com Conventional Commits
type: manual
invoke: /commit
preferences:
  commit_format: single-line
  include_coauthor: false
---

# /commit — Preparar e Validar Commit

Invoke com `/commit` quando estiver pronto para commitar mudanças. Esta Skill:

1. Verifica estado atual da working tree (`git status`)
2. Analisa staged e unstaged changes
3. Examina o diff completo
4. Identifica responsabilidades distintas
5. Sugere commits separados se apropriado
6. Valida secrets/debug antes de commitar
7. Propõe mensagem Conventional Commit

## Conventional Commits

Formato (linha única):
```
<type>(<scope>): <subject>
```

**Types:**
- `feat` — Nova funcionalidade
- `fix` — Correção de bug
- `refactor` — Mudança de código sem alterar comportamento
- `test` — Novo teste ou teste corrigido
- `docs` — Mudança em documentação
- `chore` — Setup, deps, config (sem impacto em código funcional)
- `perf` — Melhoria de performance
- `ci` — Mudança em CI/CD

**Exemplos válidos:**
- `feat(auth): add JWT token generation`
- `fix(tenancy): ensure tenant_id filter in all queries`
- `test(reserva): add regression test for concurrent reservation`
- `docs(CLAUDE.md): update context navigation section`

**Exemplos inválidos:**
- `fix stuff` — vago
- `updates` — qual mudança?
- `ajustes` — não descreve problema/solução
- `WIP` — não commita assim

## Validações

Esta Skill valida:

- ✅ Nenhum `print()` de debug
- ✅ Nenhum `console.log()` pendente
- ✅ Nenhum `TODO`/`FIXME` sem issue
- ✅ Nenhum `breakpoint()`/`pdb`
- ✅ Nenhum arquivo de secrets (`.env`, `*.key`, `*.pem`)
- ✅ Nenhuma senha ou token em código
- ✅ Mudanças relacionadas agrupadas (ou sugerir split)
- ✅ Mensagem clara e significativa

## Quando invocar

✅ Quando pronto para commitar mudanças locais.

❌ Não use se ainda estiver editando/testando.

## Exemplo de workflow

```bash
# ... você edita arquivos, roda testes ...
$ /commit

# Claude analisa e sugere:
# "Detectei 2 responsabilidades distintas:
#  1. feat(tenancy): criar modelo Tenant
#  2. test(tenancy): add fixtures
# Gostaria que sejam commits separados? (S/n)"

# Você escolhe. Depois Claude propõe mensagem Conventional Commit.

# Se tudo estiver ok, Claude executa `git commit`.
```

## Após commit

- Mensagem registrada em git log (navegável depois).
- Se código importante for exigido em outra sessão, outro dev encontra no commit message ou diff.

---

## Checklist — Antes de Chamar /commit

- [ ] Testes passam localmente
- [ ] Lint/format (`ruff`, `black`) ok
- [ ] Type check (`mypy`, `pyright`) ok
- [ ] Nenhum `print()` de debug
- [ ] Nenhum `TODO` solto
- [ ] Nenhum arquivo acidental (`.env`, `__pycache__`, `.pyc`)
- [ ] Mensagem vai descrever claramente a mudança
