"""FastAPI app factory + lifespan.

Lifespan owns all startup-time resource resolution (Engineering Standards chapter 3).
Phase 3: Vault -> DB engine -> Redis (fastapi-cache2 + fastapi-limiter) -> Casbin enforcer
-> refuse-to-start checks (BOOT-01, BOOT-02).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import structlog
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_limiter import FastAPILimiter

from app.api import admin, audit, auth, batches, health, predictions, users
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.request_id import RequestIdMiddleware
from app.core.vault import VaultUnreachable, resolve_secrets
from app.db.session import make_engine, make_sessionmaker
from app.infra.casbin.enforcer import build_enforcer, policy_row_count

logger = structlog.get_logger(__name__)


def _to_sync_url(async_url: str) -> str:
    """Convert postgresql+asyncpg URL to postgresql+psycopg2 for Casbin adapter."""
    return async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Phase 3 lifespan: Vault -> DB -> Redis -> Casbin -> refuse-to-start."""
    configure_logging()
    settings = get_settings()

    # BOOT-01: Vault must be reachable.
    try:
        secrets = resolve_secrets()
    except VaultUnreachable as exc:
        logger.error("vault_unreachable", error=str(exc))
        raise

    app.state.secrets = secrets

    # DB engine + sessionmaker. Tests set DROPSORT_DB_NULL_POOL=1 to avoid cross-test
    # asyncpg connection state leaking when create_app() runs multiple times in one
    # process.
    import os as _os

    use_null_pool = _os.environ.get("DROPSORT_DB_NULL_POOL", "").lower() in ("1", "true")
    engine = make_engine(secrets.postgres_url, use_null_pool=use_null_pool)
    app.state.db_engine = engine
    app.state.db_sessionmaker = make_sessionmaker(engine)
    logger.info("db_engine_ready", null_pool=use_null_pool)

    # Redis: TWO clients.
    # - cache_redis: decode_responses=False - fastapi-cache2's JsonCoder calls .decode() on values.
    # - limiter_redis: decode_responses=True - fastapi-limiter expects str responses.
    # Both share the same Redis server / db number.
    cache_redis = aioredis.from_url(secrets.redis_url, encoding="utf-8", decode_responses=False)
    limiter_redis = aioredis.from_url(secrets.redis_url, encoding="utf-8", decode_responses=True)
    app.state.redis = limiter_redis  # exposed for /health (text response from ping is fine)
    app.state.cache_redis = cache_redis
    FastAPICache.init(RedisBackend(cache_redis), prefix="dropsort-cache")
    await FastAPILimiter.init(limiter_redis)
    logger.info("cache_and_limiter_ready")

    # BOOT-02: Casbin policy table must be non-empty + enforcer loaded.
    sync_pg_url = _to_sync_url(secrets.postgres_url)
    print(sync_pg_url)
    rows = policy_row_count(sync_pg_url)
    if rows == 0:
        msg = "BOOT-02: casbin_rule table is empty. Did you run `alembic upgrade head`?"
        logger.error("casbin_policy_empty", message=msg)
        raise RuntimeError(msg)

    enforcer = build_enforcer(sync_pg_url)
    enforcer.load_policy()
    app.state.casbin_enforcer = enforcer
    logger.info("casbin_enforcer_loaded", policy_rows=rows)

    # BOOT-03 + BOOT-04: classifier weights present, SHA matches, test_top1 above threshold.
    from app.classifier.boot_checks import (
        verify_classifier_present,
        verify_classifier_sha,
        verify_classifier_top1_above_threshold,
    )

    verify_classifier_present()
    verify_classifier_sha()
    verify_classifier_top1_above_threshold()
    logger.info("classifier_boot_checks_passed")

    logger.info(
        "app_ready",
        log_level=settings.log_level,
        api_port=settings.api_port,
        phase="api-auth-casbin",
    )
    yield

    # Shutdown order: limiter -> redis clients -> engine. FastAPICache has no close().
    # Class-level singletons (FastAPICache._backend etc.) are intentionally NOT reset:
    # the next create_app() lifespan calls .init() again which rebinds them. Resetting
    # to None mid-shutdown was racy when LifespanManager teardown overlapped with a
    # subsequent test's request.
    await FastAPILimiter.close()
    # `close()` works across redis-py 4.x/5.x; aclose() is 5.x-only.
    await cache_redis.close()
    await limiter_redis.close()
    await engine.dispose()

    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Application factory. Each test gets a fresh app (fresh lifespan).

    Production uvicorn invocation:
        uvicorn app.main:create_app --factory
    """
    app = FastAPI(title="dropsort", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth")
    app.include_router(users.router)
    app.include_router(batches.router)
    app.include_router(predictions.router)
    app.include_router(admin.router)
    app.include_router(audit.router)
    return app


# Uvicorn entrypoints:
#   uvicorn app.main:create_app --factory      # preferred (production)
#   uvicorn app.main:app                       # also works via the lazy `app`
#
# `app` is intentionally NOT built at module-import time. Building it would trigger
# lifespan side effects (Vault read, DB engine creation, FastAPICache.init) during
# any `from app.main import ...` - which polluted test isolation. Tests import
# `create_app` directly and build per-fixture.
def _get_app() -> FastAPI:
    """Lazy singleton for `uvicorn app.main:app` invocation pattern."""
    global _app  # noqa: PLW0603
    if _app is None:
        _app = create_app()
    return _app


_app: FastAPI | None = None


def __getattr__(name: str) -> FastAPI:
    """PEP 562 module-level __getattr__ - resolves `app` on first access only."""
    if name == "app":
        return _get_app()
    raise AttributeError(f"module 'app.main' has no attribute {name!r}")
