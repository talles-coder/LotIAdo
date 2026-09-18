---
name: testing
description: Padrões de testes (pytest, fixtures, integração) para projeto LotIAdo
type: code-review
trigger: [create-test, edit-test]
applies-to: ["**/test_*.py", "**/*_test.py"]
---

# Testes — Padrões do Projeto LotIAdo

Esta Skill se carrega quando você cria/edita testes ou quando uma funcionalidade exige cobertura de testes.

## pytest — Setup

### Configuração (pytest.ini / pyproject.toml)
```ini
[tool:pytest]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "-v --tb=short"
```

### Fixtures — conftest.py
Centralizar em um único `conftest.py` raiz para BD e cliente HTTP de teste.

## Testes Unitários (domain)

Testes de **regra de negócio pura**, sem BD/HTTP:

```python
def test_lote_pode_reservar():
    """Lote em estado 'disponível' pode ser reservado."""
    lote = Lote(id=uuid4(), status=LoteStatus.DISPONIVEL)
    assert lote.pode_reservar() is True
```

**Princípios:**
- Testa comportamento (o que muda), não detalhes (como funciona).
- Nome explícito: `test_<função>_<cenário>()`.

## Testes de Integração (com BD)

Testes de **fluxo completo** (domain + infrastructure + application):

```python
@pytest.mark.asyncio
async def test_criar_reserva_com_sucesso(db, tenant_id):
    """Usuário consegue criar reserva de lote disponível."""
    lote = await create_lote_in_db(db, tenant_id, status=LoteStatus.DISPONIVEL)
    service = ReservaService(db)
    reserva = await service.criar_reserva(lote_id=lote.id, tenant_id=tenant_id)
    assert reserva.status == ReservaStatus.ATIVA
```

## Testes de API (HTTP)

Testes de **endpoint FastAPI** (interface):

```python
@pytest.mark.asyncio
async def test_login_com_sucesso(client, db):
    """Login com credenciais corretas retorna JWT."""
    await create_user_in_db(db, email="test@test.com", password="senha123")
    response = await client.post("/auth/login", json={
        "email": "test@test.com", "password": "senha123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Parametrização

```python
@pytest.mark.parametrize("status,pode_reservar", [
    (LoteStatus.DISPONIVEL, True),
    (LoteStatus.VENDIDO, False),
])
def test_lote_pode_reservar(status, pode_reservar):
    lote = Lote(id=uuid4(), status=status)
    assert lote.pode_reservar() is pode_reservar
```

## Mocks — Use com cuidado

Mock recursos externos (Ollama, MinIO) em testes unitários. Use integração real em testes de integração.

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_chunk_documento_chama_ollama(monkeypatch):
    mock_llm = AsyncMock()
    mock_llm.embed.return_value = [0.1, 0.2, 0.3]
    monkeypatch.setattr("app.ai_rag.llm_provider", mock_llm)
    result = await chunk_e_embed("doc.pdf")
    mock_llm.embed.assert_called()
```

## Isolamento e Determinismo

- Cada teste começa com BD limpa (rollback após teste).
- Sem estado compartilhado entre testes.
- Sem `random.random()` em testes — use seeds fixos.

## Testes de Regressão

Quando um bug é corrigido, adicione teste que o reproduza:

```python
@pytest.mark.asyncio
async def test_reserva_nao_dobrada_concorrencia(db):
    """Regression: lock previne duas reservas do mesmo lote."""
    lote = await create_lote_in_db(db, status=LoteStatus.DISPONIVEL)
    service = ReservaService(db)
    task1 = service.criar_reserva(lote_id=lote.id)
    task2 = service.criar_reserva(lote_id=lote.id)
    results = await asyncio.gather(task1, task2, return_exceptions=True)
    assert sum(isinstance(r, Reserva) for r in results) == 1
    assert sum(isinstance(r, LoteJaReservado) for r in results) == 1
```

## Coverage

```bash
pytest --cov=app --cov-report=html
```

Meta: **>80% em domain**, **>70% em application**.

---

## Checklist

- [ ] Testes passam (`pytest`).
- [ ] Nomes claros e descritivos.
- [ ] Setup/Act/Assert separados.
- [ ] Async tests com `@pytest.mark.asyncio`.
- [ ] BD reset entre testes.
- [ ] Coverage aceitável.
- [ ] Nenhum `print()` ou `breakpoint()`.
