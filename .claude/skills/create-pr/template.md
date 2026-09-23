# PR Template — LotIAdo

## Resumo

**Tarefa:** [Link para task no backlog / Jira se houver]

**Problema/Contexto:**
Explique brevemente o problema que resolve ou funcionalidade que adiciona.

**Solução:**
Como foi resolvido. Abordagem adotada.

---

## Alterações Principais

- Arquivo 1: o que mudou (X linhas)
- Arquivo 2: o que mudou (Y linhas)
- (Se muitas mudanças, agrupar por módulo)

---

## Como Testar

```bash
# Passos para validar a mudança
pytest tests/test_auth.py -v
# Ou manual:
# 1. Login via POST /auth/login com email/senha
# 2. Verificar que JWT retorna
# 3. Acessar GET /auth/me com o token — deve retornar usuário
```

---

## Evidências

(Apenas se relevante — screenshots, logs, exemplos)

**Request/Response:**
```json
POST /auth/login
{"email": "test@test.com", "password": "password123"}

200 OK
{"access_token": "eyJh...", "token_type": "bearer"}
```

---

## Riscos / Impactos

(Só se houver algo não óbvio — migrations, breaking changes, performance, segurança, etc)

- [ ] Não há
- [ ] Migrations necessárias (descrição breve)
- [ ] Breaking change em API (versão muda?)
- [ ] Impacto em performance (qual é?)
- [ ] Segurança impactada (como?)
- [ ] Multi-tenancy impactada (qual cenário?)

---

## Checklist

- [ ] Escopo da tarefa respeitado
- [ ] Documentação relevante (docs/) consultada
- [ ] Testes adicionados/atualizados quando necessário
- [ ] Testes passando (pytest)
- [ ] Lint/format/type check passando
- [ ] Nenhum secrets ou credenciais
- [ ] Nenhum arquivo acidental (`.env`, `__pycache__`, etc)
- [ ] Nenhuma alteração não relacionada (no refactors extras)
- [ ] Documentação atualizada quando necessário (README, docs/, CLAUDE.md)
- [ ] PR compreensível por outro dev sem contexto da conversa

---

*Deletar seções que não se aplicam (como "Riscos" se não há). PR muito longo = sinal de escopo grande demais.*
