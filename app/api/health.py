"""Health router.

Deps reported: postgres, redis, vault, casbin_policy, minio, classifier.
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request, Response, status

from app.core.request_id import get_current_request_id
from app.core.vault import health_check as vault_health
from app.infra.minio_storage import MinioStorage

_CLASSIFIER_WEIGHTS = (
    Path(__file__).resolve().parent.parent / "classifier" / "models" / "classifier.pt"
)

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


async def _check_minio() -> dict[str, Any]:
    start = time.monotonic()
    try:
        storage = MinioStorage()
        exists = await asyncio.to_thread(storage.client.bucket_exists, storage.bucket_name)
        return {
            "status": "ok" if exists else "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            **({} if exists else {"error": f"bucket '{storage.bucket_name}' missing"}),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            "error": str(exc)[:200],
        }


async def _check_classifier() -> dict[str, Any]:
    start = time.monotonic()
    try:
        present = await asyncio.to_thread(_CLASSIFIER_WEIGHTS.is_file)
        return {
            "status": "ok" if present else "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            **({} if present else {"error": "classifier.pt missing"}),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "fail",
            "latency_ms": int((time.monotonic() - start) * 1000),
            "error": str(exc)[:200],
        }


@router.get("/health")
async def health(request: Request, response: Response) -> dict[str, Any]:
    deps = {
        "postgres": await _check_postgres(request),
        "redis": await _check_redis(request),
        "vault": await _check_vault(request),
        "casbin_policy": await _check_casbin(request),
        "minio": await _check_minio(),
        "classifier": await _check_classifier(),
    }
    all_ok = all(d["status"] == "ok" for d in deps.values())
    if not all_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "ok": all_ok,
        "request_id": get_current_request_id(),
        "deps": deps,
    }
