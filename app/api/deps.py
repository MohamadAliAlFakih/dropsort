"""FastAPI dependency helpers.

Routers depend on these (and on service functions). No SQLAlchemy import in routers
(API-02); permission gating wraps Casbin enforce.

Note on API-02: this module imports `app.db.models.User` for the CurrentUser type
annotation only - not for SQL access. The literal `from sqlalchemy` is NOT here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User as UserORM
from app.services.auth_service import current_active_user_factory


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Yields a session from the lifespan-built sessionmaker."""
    factory = request.app.state.db_sessionmaker
    async with factory() as session:
        yield session


current_active_user = current_active_user_factory()
CurrentUser = Annotated[UserORM, Depends(current_active_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]


def require_permission(resource_pattern: str, action: str):
    """FastAPI dependency factory that enforces Casbin permission.

    Usage:
        @router.get(..., dependencies=[Depends(require_permission("/audit", "GET"))])
    """

    async def _enforce(
        request: Request, user: UserORM = Depends(current_active_user)
    ) -> None:
        enforcer = request.app.state.casbin_enforcer
        allowed = enforcer.enforce(user.role, resource_pattern, action)
        if not allowed:
            # AUTH-03: authenticated but unauthorized -> 403
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )

    return _enforce
