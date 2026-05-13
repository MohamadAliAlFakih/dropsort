"""Auth router. POST /auth/jwt/login only. POST /auth/register is intentionally NOT mounted
per CONTEXT D-05 (admin-invite only).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi_limiter.depends import RateLimiter

from app.services.auth_service import auth_backend, fastapi_users

router = APIRouter(tags=["auth"])

# Rate-limited login per CONTEXT D-06 + AUTH-08.
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
