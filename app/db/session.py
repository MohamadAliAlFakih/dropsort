"""Async DB engine + sessionmaker factory.

Engine built in `app/main.py`'s lifespan, stored on `app.state.db_engine`. Routers consume
sessions via `Depends(get_session)` defined in `app/api/deps.py`.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool


def make_engine(database_url: str, *, use_null_pool: bool = False) -> AsyncEngine:
    """Build the async engine. Caller wires this into lifespan.

    use_null_pool=True forces a fresh connection per checkout - useful for tests where
    each create_app() lifespan resolves to a separate asyncio loop. In production we
    want the default pool for perf.
    """
    if use_null_pool:
        return create_async_engine(database_url, poolclass=NullPool, pool_pre_ping=True)
    return create_async_engine(database_url, pool_size=5, max_overflow=10, pool_pre_ping=True)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
