"""Importa todos os models de domínio para registrar no SQLAlchemy declarative registry.

`relationship("Tenant")` (referência por string, usada em Cliente/Corretor)
só resolve se a classe `Tenant` já tiver sido importada em algum lugar do
processo antes da primeira query — SQLAlchemy só enxerga classes que o
Python já executou. Como nada no caminho real da aplicação (só rotas ->
services -> repositories -> domain) importa `app.tenancy.domain.models`
diretamente, a primeira query feita pela API (ex.: POST /auth/login)
disparava `InvalidRequestError: ... failed to locate a name ('Tenant')`.

Este módulo existe só para ter esse efeito colateral de import — importado
uma vez em `app.database`, cobre todos os models existentes (e, se um novo
módulo repetir o mesmo padrão de relationship por string, os futuros).
"""
from app.clientes.domain.models import Cliente  # noqa: F401
from app.corretores.domain.models import Corretor  # noqa: F401
from app.identity.domain.models import User, UserTenantMembership  # noqa: F401
from app.tenancy.domain.models import Tenant  # noqa: F401
