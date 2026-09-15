"""Alembic environment script for async migrations."""
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# `app` is importable without a manual sys.path hack because alembic.ini sets
# `prepend_sys_path = .`, which Alembic prepends to sys.path using the
# directory it's invoked from (backend/, where alembic.ini lives).
from app.common.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Migrations rodam com um papel dono das tabelas (precisa poder ALTER TABLE
# ... ENABLE/FORCE ROW LEVEL SECURITY e CREATE POLICY) — diferente do papel
# restrito que a aplicação usa em runtime (`DATABASE_URL`), para que a RLS
# ativada em FASE2-IMPL-01 realmente seja aplicada. Cai de volta pra
# `DATABASE_URL` se `MIGRATIONS_DATABASE_URL` não estiver setada.
_migrations_url = os.getenv("MIGRATIONS_DATABASE_URL") or os.getenv("DATABASE_URL", "")
config.set_main_option("sqlalchemy.url", _migrations_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = os.getenv("MIGRATIONS_DATABASE_URL") or os.getenv("DATABASE_URL", "")

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
