"""Health router (Phase 1).

Per CONTEXT D-12: returns {ok, request_id, deps: {}} with a TODO listing the deps later
phases must populate. Avoids stubbing 'pending' states that would fall out of sync.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.request_id import get_current_request_id

router = APIRouter(tags=["health"])


# TODO Phase 3/4/5: populate `deps` with readiness checks for postgres, redis, minio, vault,
# casbin_policy, classifier. Each entry: {status: "ok" | "fail", error?: str, latency_ms?: int}.
# When a dep is unhealthy the overall `ok` flips to false and HTTP 503 is returned.
@router.get("/health")
async def health() -> dict[str, Any]:
    """Liveness + dependency readiness envelope. Phase 1 returns an empty deps map."""
    return {"ok": True, "request_id": get_current_request_id(), "deps": {}}
