"""FastAPI-cache binding for RQ worker async jobs.

The API process initializes ``FastAPICache`` in ``lifespan``; the inference worker does
not. Without ``init``, ``FastAPICache.clear`` in ``record_prediction`` / ``mark_batch_failed``
cannot reach Redis, so list/detail/recent caches stay stale.

Each ``asyncio.run(...)`` job uses a **new** event loop, so we create a short-lived async
Redis client per job, init the cache backend on that loop, then reset after the coroutine
finishes (mirrors test ``FastAPICache.reset`` patterns in ``conftest.py``).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from app.core.vault import resolve_secrets


@asynccontextmanager
async def worker_cache_context() -> AsyncIterator[None]:
    """Use inside worker ``asyncio.run`` coroutines that call ``FastAPICache.clear``."""
    FastAPICache.reset()
    secrets = resolve_secrets()
    redis_client = aioredis.from_url(
        secrets.redis_url,
        encoding="utf-8",
        decode_responses=False,
    )
    FastAPICache.init(RedisBackend(redis_client), prefix="dropsort-cache")
    try:
        yield
    finally:
        await redis_client.close()
        FastAPICache.reset()
