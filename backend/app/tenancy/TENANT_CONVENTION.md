# Convenção de tenant_id

## Objetivo

Garantir o isolamento de dados entre tenants em todas as tabelas de domínio.

**Fase 2 (FASE2-IMPL-01):** RLS está ativa em `clientes`, `corretores`,
`loteamentos`, `lotes` e `audit_log` — ver migration
`20260915160000_enable_rls_on_domain_tables.py`. Toda rota que acessa essas
tabelas deve usar `Depends(get_tenant_scoped_db)`
(`app/tenancy/interface/dependencies.py`) no lugar de `Depends(get_db)`, que
seta `app.tenant_id` na sessão a partir do JWT antes de qualquer query — sem
isso a policy derruba a query pra zero linhas (fail-closed), inclusive para
o dono legítimo dos dados. `user_tenant_membership`, `users` e `tenants`
ficam de fora da RLS de propósito (são as tabelas usadas para *resolver* o
tenant no login, antes de haver um `app.tenant_id` de sessão).

Atenção: `app.tenant_id` só vale para a transação corrente (`SET LOCAL`,
via `set_config(..., true)`). Um `db.commit()` no meio da request encerra
essa transação — qualquer query feita depois (ex.: `db.refresh()`) roda sem
tenant setado e falha fechada. Por isso os repositórios não chamam
`db.refresh()` após `commit()` (a sessão já tem `expire_on_commit=False`).

## Padrão

Toda tabela de domínio **deve** ter:

1. **Coluna `tenant_id`** do tipo `UUID`, **não-nula**
   ```python
   tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
   ```

2. **Relacionamento com a tabela `tenants`**
   ```python
   from sqlalchemy.orm import relationship
   tenant = relationship("Tenant", back_populates="...")
   ```

3. **Filtro de tenant em toda query**
   ```python
   # Sempre filtrar por tenant_id, mesmo que RLS ainda não esteja ativo
   query = select(MyEntity).where(MyEntity.tenant_id == tenant_id)
   ```

## Exemplo

```python
from uuid import UUID
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.common.models import BaseModel
from app.tenancy.domain.models import Tenant

class Loteamento(BaseModel):
    """Loteamento (desenvolvimento imobiliário)."""
    __tablename__ = "loteamentos"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    
    tenant = relationship("Tenant")
```

## Por que?

- **Segurança:** Defesa em profundidade — não depender apenas de RLS ou camada de aplicação.
- **Preparação:** Quando RLS for ativado na Fase 2, o padrão já estará implantado.
- **Clareza:** Deixa explícito no código que dados são tenant-scoped.
- **Performance:** Permite índices e particionamento futuro por tenant_id.

## Checklist para novos módulos

- [ ] Modelo tem `tenant_id: UUID` não-nulo?
- [ ] Migration inclui FK para `tenants.id`?
- [ ] Serviço de aplicação filtra por `tenant_id` em select?
- [ ] Testes criam dados com `tenant_id` explícito?
