---
name: python-fastapi
description: Padrões e boas práticas para Python/FastAPI no projeto LotIAdo
type: code-review
trigger: [create-python, edit-python, create-fastapi, edit-fastapi]
applies-to: ["*.py"]
---

# Python + FastAPI — Padrões do Projeto LotIAdo

Esta Skill se carrega automaticamente quando você cria/edita código Python ou FastAPI. **Decisões específicas em `docs/` têm prioridade sobre recomendações genéricas.**

## Python — Fundamentos

### Type hints obrigatórios
- Use type hints em **toda assinatura de função**. Evite `Any` — use `T` (TypeVar) ou `Union` quando genérico for necessário.
- Dataclasses para valores imutáveis ou agregados simples (ex: `@dataclass(frozen=True)` para DTOs).
- Enums para estados/opções fechadas (ex: status de lote, papéis de usuário).

### Nomes e legibilidade
- Nomes descritivos e únicos: `get_available_lots_for_tenant()` em vez de `get_lots()`.
- Funções pequenas: máximo 15–20 linhas de lógica (testes rodam sozinhos).
- Responsabilidade única: uma função, uma tarefa clara.

### Exceções
- Defina exceções customizadas por módulo (ex: `loteamentos_lotes/domain/exceptions.py`).
- Nunca `pass` em `except` — sempre logue ou re-raise com contexto.
- Exceções no **domain** (regra de negócio), não no infrastructure (acesso a BD).

### Async/await
- Use `async def` em toda rota FastAPI e em chamadas I/O (BD, Ollama, Redis).
- Nunca `asyncio.run()` ou `await` em síncrono — estruture como async desde o início.
- Gerenciamento de recursos: use `async with` para conexões, contextos.

### Logging e debugging
- `import logging; logger = logging.getLogger(__name__)` — estruturado, não `print()`.
- Logue contexto importante (user_id, tenant_id, ação), não "função chamada".
- Sem `print()` de debug para repo — temporário? Remove antes de commit.

### Configuração
- Arquivo único `config.py` (ou `settings.py`) com `pydantic.BaseSettings`.
- Leia de `.env` / variáveis de ambiente, não hard-code.
- Valores sensíveis (secrets, credenciais) **nunca** em repo — sempre env vars.

## FastAPI — Padrões do Projeto

### Estrutura por módulo
Cada módulo (ex: `tenancy/`, `identity/`) organiza como:
```
tenancy/
├── domain/           # Entidades, regras, exceptions
├── application/      # Use cases, serviços de aplicação
├── infrastructure/   # Acesso a Postgres, Redis, etc
└── interface/        # Rotas FastAPI
```

### Rotas FastAPI
- Use **routers** por módulo, monte em `main.py`.
- Dependency injection via `Depends()` — nunca globals ou singletons diretos.
- Validação Pydantic em schemas (request/response), não em função.
- Status codes corretos: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found, 409 Conflict, 422 Unprocessable Entity.

### Separação HTTP ↔ Domínio
- Rota FastAPI é **interface** — recebe JSON Pydantic, chama serviço de aplicação, retorna JSON.
- Serviço de aplicação é **use case** — orquestra domain + infrastructure, sem conhecer HTTP.
- Domain é **regras** — máquina de estados, validações, lógica pura (não conhece BD).

Exemplo:
```python
# interface/routers.py
@router.post("/reservas")
async def criar_reserva(req: CriarReservaRequest, service: ReservaService = Depends()):
    resultado = await service.criar_reserva(req.lote_id, req.cliente_id)
    return resultado

# application/services.py
class ReservaService:
    async def criar_reserva(self, lote_id: UUID, cliente_id: UUID) -> Reserva:
        lote = await self.repository.get_lote(lote_id)
        if not lote.pode_reservar():  # domain logic
            raise LoteNaoDisponivel()
        return await self.repository.create_reserva(...)

# domain/entities.py
class Lote:
    def pode_reservar(self) -> bool:
        return self.status == LoteStatus.DISPONIVEL
```

### Schemas Pydantic
- Use schemas separados para request/response quando necessário (ex: `CriarUsuarioRequest` vs `UsuarioResponse` sem senha).
- Validação customizada: `@field_validator` inline no schema.
- Avoid `Config.arbitrary_types_allowed = True` — serialize estruturas complexas como JSON.

### Autenticação e tenant
- Middleware resolve `tenant_id` do JWT, passa no request state.
- Função dependency: `get_current_user()` e `get_current_tenant()`.
- Toda query de BD já filtra por `tenant_id` automaticamente (ou via RLS na Fase 2).

### Transactions
- Serviço de aplicação abre transação: `async with db.begin()`.
- Rollback automático em exceção; commit ao sair do bloco.

## Banco de Dados (SQLAlchemy async)

### Models ORM
- Definir em `infrastructure/models.py` por módulo.
- Colunas com tipos explícitos: `UUID`, `String(255)`, `Integer`, `JSON`, `JSONB`.
- Foreign keys com `ForeignKey("tabela.coluna")`, índices úteis.
- Timestamps: `created_at` (default `datetime.utcnow`), `updated_at` (default `datetime.utcnow`, onupdate).

### Migrations (Alembic)
- Gerada: `alembic revision --autogenerate -m "add users table"`.
- Review antes de commitar — Alembic nem sempre acerta.
- Sem "drop" de coluna/tabela sem bom motivo — considere soft delete / marcação.

### Queries
```python
# Async SQLAlchemy
from sqlalchemy import select

async def get_lot(db: AsyncSession, lote_id: UUID, tenant_id: UUID) -> Lote:
    stmt = select(LoteModel).where(
        LoteModel.id == lote_id,
        LoteModel.tenant_id == tenant_id  # sempre filtrar por tenant
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

## PostGIS + pgvector (Fase 2+, Fase 7+)

- **PostGIS queries:** Sempre em infrastructure, wrappadas em serviço.
- **pgvector (embeddings):** Filtro de `tenant_id` explícito em toda query (`WHERE tenant_id = ...`).
- Sem raw SQL cru — use SQLAlchemy core ou ORM com type safety.

## Testes (ver Skill `testing`)

- Toda lógica de domain tem teste unitário.
- Endpoint tem teste de integração (com BD de teste real, não mock).
- Fixtures de banco e cliente HTTP em `conftest.py`.

## Decisões do Projeto LotIAdo

| Decisão | O que fazer | Por que | Exceção |
|---|---|---|---|
| Backoffice web = Expo for Web | Nunca crie templates server-rendered (Jinja2) | Backend é API pura, frontend é app Expo único | Nenhuma (Fase 11 cloud pode divergir, mas core mantém isso) |
| Monólito modular | Organize por domínio (vertical), não por camada (horizontal) | Coesão domínio > acoplamento técnico | Infra compartilhada (BD, Redis) vive em `shared/` |
| Offline só leitura | Nunca implemente fila de sincronização | MVP deliberado, simplifica dados e conflitos | Fase 11 pode evoluir |
| RLS sem exceção | RLS ativado Fase 2, antes: filtro em toda query | Evita vazamento de tenant em futuro | Nenhuma — é rule-of-the-road |

---

## Checklist — Antes de Commitar

- [ ] Type hints em toda função.
- [ ] Nenhum `Any` a não ser TypeVar genérico.
- [ ] Nenhum `print()` de debug.
- [ ] Mensagens de erro descritivas, não "error".
- [ ] Exceções customizadas (domain) em `exceptions.py`.
- [ ] Logging em vez de `print()`.
- [ ] Testes passando (locais).
- [ ] Lint (`ruff`, `pylint`) sem warnings.
- [ ] Type check (`mypy` ou `pyright`) sem erros.
- [ ] Documentação atualizada (docstrings com purpose, não "do X").
- [ ] Sem código morto ou importações não usadas.
