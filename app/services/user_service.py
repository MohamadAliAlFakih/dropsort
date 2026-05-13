"""User service: change_role, invite. Owns transactions + cache invalidation (API-04)."""

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
    # Invalidates ALL /me cache entries. Acceptable: /me cache is tiny and clearing
    # the whole namespace guarantees the target user sees the new role on next call.
    await FastAPICache.clear(namespace="me")
    logger.info(
        "role_changed", target=str(target_user_id), role_from=current.role, role_to=new_role
    )
    return updated


async def invite(
    *,
    session: AsyncSession,
    email: str,
    password: str,
    role: str,
    actor_id: UUID,
) -> UserOut:
    """Admin-only. Creates user + audit row in one transaction."""
    from passlib.context import CryptContext

    ctx = CryptContext(schemes=["argon2"], deprecated="auto")
    hashed = ctx.hash(password)

    async with session.begin():
        existing = await user_repository.get_by_email(session, email)
        if existing is not None:
            raise UserAlreadyExists(email)
        user = await user_repository.create(
            session, email=email, hashed_password=hashed, role=role
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
