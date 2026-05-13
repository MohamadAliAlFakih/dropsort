"""Admin router. CONTEXT D-05: only admin creates users. Casbin gates /admin/* to admin."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi_limiter.depends import RateLimiter

from app.api.deps import CurrentUser, DbSession, require_permission
from app.domain import RoleChangeIn, UserCreate, UserOut
from app.repositories import user_repository
from app.services.user_service import UserAlreadyExists, UserNotFound, change_role, invite

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=list[UserOut],
    dependencies=[Depends(require_permission("/admin/users", "GET"))],
)
async def list_users_endpoint(
    session: DbSession, _user: CurrentUser
) -> list[UserOut]:
    return list(await user_repository.list_all(session))


@router.post(
    "/users/invite",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_permission("/admin/users/invite", "POST")),
        Depends(RateLimiter(times=10, seconds=60)),
    ],
)
async def invite_user_endpoint(
    session: DbSession,
    user: CurrentUser,
    body: UserCreate,
) -> UserOut:
    try:
        return await invite(
            session=session,
            email=body.email,
            password=body.password,
            role=body.role,
            actor_id=user.id,
        )
    except UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from None


@router.post(
    "/users/{target_user_id}/role",
    response_model=UserOut,
    dependencies=[
        Depends(require_permission("/admin/users/{target_user_id}/role", "POST"))
    ],
)
async def change_role_endpoint(
    request: Request,
    session: DbSession,
    user: CurrentUser,
    target_user_id: UUID,
    body: RoleChangeIn,
) -> UserOut:
    enforcer = request.app.state.casbin_enforcer
    try:
        return await change_role(
            session=session,
            target_user_id=target_user_id,
            new_role=body.role,
            actor_id=user.id,
            enforcer=enforcer,
        )
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        ) from None
