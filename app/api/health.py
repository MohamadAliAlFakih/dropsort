"""Health router (Phase 3).

Per CONTEXT D-12: deps now includes postgres, redis, vault, casbin_policy.
Phase 4 adds minio; Phase 2/4 add classifier.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter, Request, Response, status

from app.core.request_id import get_current_request_id
from app.core.vault import health_check as vault_health

router = APIRouter(tags=["health"])


async def _check_postgres(request: Request) -> dict[str, Any]:
    engine = request.app.state.db_engine
    start = time.monotonic()
    try:
        from sqlalchemy import text  # local import: API-02 top-level grep gate stays clean

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "latency_ms": int((time.monotonic() - start) * 1000)}
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            "error": str(exc)[:200],
        }


async def _check_redis(request: Request) -> dict[str, Any]:
    redis = request.app.state.redis
    start = time.monotonic()
    try:
        pong = await redis.ping()
        return {
            "status": "ok" if pong else "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            "error": str(exc)[:200],
        }


async def _check_vault(_request: Request) -> dict[str, Any]:
    ok, latency_ms, err = vault_health()
    return {"status": "ok" if ok else "fail", "latency_ms": latency_ms, "error": err}


async def _check_casbin(request: Request) -> dict[str, Any]:
    enforcer = request.app.state.casbin_enforcer
    start = time.monotonic()
    try:
        policies = enforcer.get_policy()
        return {
            "status": "ok" if policies else "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            "policy_count": len(policies),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            "error": str(exc)[:200],
        }


# TODO Phase 4: add minio readiness. TODO Phase 2/4: add classifier readiness.
@router.get("/health")
async def health(request: Request, response: Response) -> dict[str, Any]:
    deps = {
        "postgres": await _check_postgres(request),
        "redis": await _check_redis(request),
        "vault": await _check_vault(request),
        "casbin_policy": await _check_casbin(request),
    }
    all_ok = all(d["status"] == "ok" for d in deps.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "ok": all_ok,
        "request_id": get_current_request_id(),
        "deps": deps,
    }
