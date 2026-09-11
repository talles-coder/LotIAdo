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
- ✅ Versões de pacotes inválidas (requirements.txt, package.json, etc)
- ✅ Encoding corrompido na descrição do PR (UTF-8 válido)

## Validações Automáticas

Tenta executar (se disponível):
- `pytest` — testes passam?
- `ruff check` — lint ok?
- `black --check` — formato ok?
- `mypy` / `pyright` — type check ok?

**Validações Obrigatórias:**
- ⚠️ **requirements.txt / package.json**: Verificar que TODAS as versões de pacotes existem (não inventadas). Validar com `pip check` ou equivalente.
- ⚠️ **Encoding da descrição do PR**: UTF-8 válido, sem caracteres corrompidos (ç,ã,é preservados corretamente)
- ⚠️ **Descrição do PR**: Sem caracteres especiais corrompidos, sem `\n` literais em lugar de quebras reais

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

## Formato do PR

Segue template em `.claude/skills/create-pr/template.md`:
- Resumo (problema, solução)
- Alterações principais
- Como testar
- Evidências (se houver)
- Riscos/impactos
- Checklist de handoff

**Título do PR:** Deve começar com o número da task, ex: `SCRUM-45: feat(backend): create FastAPI skeleton with modular structure`

## Após PR criado

- URL do PR exibida
- Nunca faz merge automaticamente
- Outro dev (ou CI) faz review

---

## Checklist — Antes de Chamar /create-pr

**Código:**
- [ ] Branch criada de `main` (ou base correta)
- [ ] Testes passam localmente
- [ ] Lint/format/type check ok
- [ ] Nenhum commit WIP ou fixup pendente
- [ ] Escopo é exatamente o que a task pede (não mais)
- [ ] Documentação atualizada (se necessário)
- [ ] Handoff é claro (outro dev sem contexto entende)
- [ ] Riscos/impactos mencionados (se houver)

**Dependências & Integridade:**
- [ ] `requirements.txt` / `package.json`: Todas as versões são VÁLIDAS e existem em PyPI / npm
  - Testar: `pip install -r requirements.txt --dry-run` ou `npm install --dry-run`
- [ ] Nenhuma versão inventada ou typo em nome de pacote
- [ ] Se alterar dependências, validar compatibilidade

**PR Body:**
- [ ] Descrição sem caracteres corrompidos (ç, ã, é aparecem corretamente)
- [ ] Encoding UTF-8 válido (sem `\n` literal em lugar de quebra real)
- [ ] Texto legível: verificar no browser antes de criar
