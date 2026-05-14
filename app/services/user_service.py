"""User service: change_role, invite, lifecycle. Owns transactions + cache invalidation (API-04)."""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import structlog
from fastapi_cache import FastAPICache
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import UserOut
from app.repositories import audit_repository, user_repository

logger = structlog.get_logger(__name__)


class UserNotFound(Exception):
    pass


class UserAlreadyExists(Exception):
    """Raised by `invite` when the email is already registered. Router maps to HTTP 409."""


class CannotActOnSelf(Exception):
    """Lifecycle or role change on the acting user's own account."""


class CannotManageAdministrator(Exception):
    """Target is an administrator; only non-admin accounts may be managed."""


class UserRemoved(Exception):
    """Target account is already soft-deleted."""


def _require_manageable_target(target: UserOut, actor_id: UUID) -> None:
    if target.deleted_at is not None:
        raise UserRemoved(str(target.id))
    if target.id == actor_id:
        raise CannotActOnSelf()
    if target.role == "admin":
        raise CannotManageAdministrator()


async def change_role(
    *,
    session: AsyncSession,
    target_user_id: UUID,
    new_role: str,
    actor_id: UUID,
    enforcer: Any,
) -> UserOut:
    """Atomic: update role + audit row + Casbin enforcer reload + cache invalidation.

    CACHE-03 + AUTH-07: role change reflects on the user's very next /me call.
    """
    async with session.begin():
        current = await user_repository.get_by_id(session, target_user_id)
        if current is None:
            raise UserNotFound(str(target_user_id))
        _require_manageable_target(current, actor_id)

        updated = await user_repository.set_role(session, target_user_id, new_role)
        if updated is None:
            raise UserNotFound(str(target_user_id))

        await audit_repository.append(
            session,
            actor_id=actor_id,
            action="role_changed",
            target_type="user",
            target_id=str(target_user_id),
            metadata={"from": current.role, "to": new_role},
        )
    # After commit: reload Casbin policy (sync I/O in a thread) + invalidate cache
    await asyncio.to_thread(enforcer.load_policy)
    await FastAPICache.clear(namespace="me")
    logger.info(
        "role_changed", target=str(target_user_id), role_from=current.role, role_to=new_role
    )
    return updated


async def set_user_active(
    *,
    session: AsyncSession,
    target_user_id: UUID,
    is_active: bool,
    actor_id: UUID,
) -> UserOut:
    async with session.begin():
        current = await user_repository.get_by_id(session, target_user_id)
        if current is None:
            raise UserNotFound(str(target_user_id))
        _require_manageable_target(current, actor_id)

        updated = await user_repository.set_is_active(session, target_user_id, is_active)
        if updated is None:
            raise UserNotFound(str(target_user_id))

        action = "user_reactivated" if is_active else "user_deactivated"
        await audit_repository.append(
            session,
            actor_id=actor_id,
            action=action,
            target_type="user",
            target_id=str(target_user_id),
            metadata={"email": current.email, "is_active": is_active},
        )
    await FastAPICache.clear(namespace="me")
    logger.info(action, target=str(target_user_id), is_active=is_active)
    return updated


async def remove_user_account(
    *,
    session: AsyncSession,
    target_user_id: UUID,
    actor_id: UUID,
) -> None:
    async with session.begin():
        current = await user_repository.get_by_id(session, target_user_id)
        if current is None:
            raise UserNotFound(str(target_user_id))
        _require_manageable_target(current, actor_id)

        updated = await user_repository.soft_delete(session, target_user_id)
        if updated is None:
            raise UserNotFound(str(target_user_id))

        await audit_repository.append(
            session,
            actor_id=actor_id,
            action="user_deleted",
            target_type="user",
            target_id=str(target_user_id),
            metadata={"prior_email": current.email},
        )
    await FastAPICache.clear(namespace="me")
    logger.info("user_deleted", target=str(target_user_id))


async def invite(
    *,
    session: AsyncSession,
    email: str,
    raw_secret: str,
    role: str,
    actor_id: UUID,
) -> UserOut:
    """Admin-only. Creates user + audit row in one transaction."""
    from passlib.context import CryptContext

    ctx = CryptContext(schemes=["argon2"], deprecated="auto")
    hashed = ctx.hash(raw_secret)

    async with session.begin():
        existing = await user_repository.get_by_email(session, email)
        if existing is not None:
            raise UserAlreadyExists(email)
        user = await user_repository.create(
            session, email=email, auth_hash=hashed, role=role
        )
        await audit_repository.append(
            session,
            actor_id=actor_id,
            action="user_invited",
            target_type="user",
            target_id=str(user.id),
            metadata={"email": email, "role": role},
        )
    logger.info("user_invited", target=str(user.id), email=email, role=role)
    return user
