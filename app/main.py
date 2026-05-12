"""FastAPI app factory + lifespan.

Lifespan owns all startup-time resource resolution (Engineering Standards chapter 3).
Phase 1 lifespan is intentionally thin - it configures logging, loads Settings, and TODO-
comments every downstream resource Phases 2/3/4 will wire in.

Module-level `app` is the uvicorn target: `uvicorn app.main:app`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.api import health
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.request_id import RequestIdMiddleware

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup -> yield -> shutdown.

    Phase 1: configure logging, resolve Settings, log a 'ready' line. That's it.
    Phase 2 (Saleh) adds: verify_classifier_present + verify_classifier_sha + top1 threshold.
    Phase 3 (Fakih) adds: Vault secret resolution, DB engine, Redis (fastapi-cache2 init),
                          Casbin enforcer load (refuse-to-start if policy table empty).
    Phase 4 (Nasser) adds: equivalent worker-side boot checks in app/workers/.
    """
    configure_logging()
    settings = get_settings()

    # TODO Phase 3: resolve secrets from Vault (BOOT-01); set on app.state.secrets.
    # TODO Phase 3: build async DB engine + sessionmaker; set on app.state.db.
    # TODO Phase 3: init fastapi-cache2 (Redis) here (CACHE-01).
    # TODO Phase 3: load Casbin enforcer (BOOT-02 - refuse to boot if policy table empty).
    # TODO Phase 2: verify classifier weights present + SHA + top1 (BOOT-03, BOOT-04).

    logger.info(
        "app_ready",
        log_level=settings.log_level,
        api_port=settings.api_port,
        phase="bootstrap",
    )
    yield
    logger.info("app_shutdown")


def create_app() -> FastAPI:
    """Application factory. Used by uvicorn and by tests (so each test gets a fresh app)."""
    app = FastAPI(
        title="dropsort",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(health.router)
    return app


# Module-level `app` is the conventional uvicorn target: `uvicorn app.main:app`.
app = create_app()
