"""Users router. Plan 03-02 ships /me; Plan 03-04 ships /admin/users/*."""

from __future__ import annotations

import hashlib
from typing import Any

from fastapi import APIRouter, Depends
from fastapi_cache.decorator import cache

from app.api.deps import CurrentUser, require_permission
from app.db.models import User as UserORM
from app.domain import UserOut

router = APIRouter(tags=["users"])


def _me_cache_key_builder(
    func: Any,
    namespace: str = "",
    *,
    request: Any = None,
    response: Any = None,
    args: Any = (),
    kwargs: Any = None,
) -> str:
    """Per-user /me cache key (CONTEXT D-09).

    fastapi-cache2 passes `namespace="dropsort-cache:me"` (prefix:namespace). The full
    Redis key becomes `dropsort-cache:me:{user_id}`. Invalidation in user_service uses
    `FastAPICache.clear(namespace="me")` which scans `dropsort-cache:me:*`.

    If the injected `user` is missing from ``kwargs`` (decorator / FastAPI edge cases),
    falling back to a hash of the ``Authorization`` header avoids a shared ``anon`` key
    that would return the wrong profile after account switching.
    """
    kwargs = kwargs or {}
    user = kwargs.get("user")
    if user is None:
        for arg in args:
            if isinstance(arg, UserORM):
                user = arg
                break

    if user is not None:
        suffix = str(user.id)
    elif request is not None:
        raw = (
            request.headers.get("authorization") or request.headers.get("Authorization") or ""
        ).encode()
        suffix = hashlib.sha256(raw).hexdigest() if raw else "anon"
    else:
        suffix = "anon"
    return f"{namespace}:{suffix}"


@router.get(
    "/me",
    response_model=UserOut,
    dependencies=[Depends(require_permission("/me", "GET"))],
)
@cache(expire=60, namespace="me", key_builder=_me_cache_key_builder)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
