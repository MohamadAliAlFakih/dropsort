"""Worker-side DB session helper.

RQ jobs run in worker processes that have NO FastAPI lifespan to set up
`app.state.db_sessionmaker`. This module builds a session factory on demand from
Vault-resolved secrets, lru-cached so each worker process pays the cost once.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.vault import resolve_secrets
from app.db.session import make_engine, make_sessionmaker


@lru_cache(maxsize=1)
def get_worker_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return a process-wide sessionmaker. Builds the engine on first call."""
    secrets = resolve_secrets()
    engine = make_engine(secrets.postgres_url)
    return make_sessionmaker(engine)
