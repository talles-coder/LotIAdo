"""Cria um tenant + usuário de teste para login manual (Postman, etc).

Uso:
    cd backend
    python -m scripts.seed_user --email user@test.com --password senha123 --tenant-slug demo
"""
import argparse
import asyncio

from sqlalchemy import select

from app.database import async_session
from app.identity.application.security import hash_password
from app.identity.domain.models import User, UserTenantMembership
from app.tenancy.domain.models import Tenant


async def seed_user(email: str, password: str, tenant_slug: str, tenant_name: str) -> None:
    async with async_session() as db:
        result = await db.execute(select(Tenant).where(Tenant.slug == tenant_slug))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(name=tenant_name, slug=tenant_slug)
            db.add(tenant)
            await db.flush()
            print(f"Tenant criado: {tenant.slug} ({tenant.id})")
        else:
            print(f"Tenant já existia: {tenant.slug} ({tenant.id})")

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is not None:
            print(f"Usuário já existia: {user.email} ({user.id}) — nada a fazer.")
            return

        user = User(email=email, hashed_password=hash_password(password), full_name="Usuário de Teste")
        db.add(user)
        await db.flush()

        db.add(UserTenantMembership(user_id=user.id, tenant_id=tenant.id, role="admin"))
        await db.commit()

        print(f"Usuário criado: {user.email} ({user.id}) — membership com tenant {tenant.slug}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", default="user@test.com")
    parser.add_argument("--password", default="senha123")
    parser.add_argument("--tenant-slug", default="demo")
    parser.add_argument("--tenant-name", default="Demo")
    args = parser.parse_args()

    asyncio.run(seed_user(args.email, args.password, args.tenant_slug, args.tenant_name))


if __name__ == "__main__":
    main()
