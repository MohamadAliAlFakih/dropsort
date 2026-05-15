"""Alembic migration environment (Phase 1).

DB URL is resolved at runtime from an env var (or a localhost default) - NOT from alembic.ini.
This honours API-06 (env vars touch only one module: env.py legitimately reads its own).

Phase 3 extends:
- Imports app.db.models so `target_metadata = Base.metadata` is populated.
- Phase 1 keeps target_metadata = None so autogenerate is a no-op (Phase 1 ships an EMPTY
  initial revision per CONTEXT D-19).
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.db.models import Base

target_metadata = Base.metadata

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _resolve_database_url() -> str:
    """Resolve DB URL.

    Phase 1: prefer explicit ALEMBIC_DATABASE_URL env var, fall back to a localhost dev URL.
    Phase 3: replace with `secrets.postgres_url` resolved from Vault during boot.
    """
    explicit = os.environ.get("ALEMBIC_DATABASE_URL")
    if explicit:
        return explicit
    return "postgresql+asyncpg://dropsort:dropsort-dev@localhost:5432/dropsort"


def run_migrations_offline() -> None:
    """Offline migrations - emits SQL to stdout instead of executing."""
    url = _resolve_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Online migrations using async engine (matches Phase 3's SQLAlchemy 2.x async setup)."""
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _resolve_database_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
