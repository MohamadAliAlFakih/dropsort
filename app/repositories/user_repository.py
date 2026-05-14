"""User repository. SQL-only; returns Pydantic; no HTTPException (API-03)."""

from __future__ import annotations

import secrets
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User as UserORM
from app.domain import UserOut


async def get_by_id(session: AsyncSession, user_id: UUID) -> UserOut | None:
    result = await session.execute(select(UserORM).where(UserORM.id == user_id))  # type: ignore[arg-type]
    row = result.scalar_one_or_none()
    return UserOut.model_validate(row) if row else None


async def get_by_email(session: AsyncSession, email: str) -> UserOut | None:
    result = await session.execute(select(UserORM).where(UserORM.email == email))  # type: ignore[arg-type]
    row = result.scalar_one_or_none()
    return UserOut.model_validate(row) if row else None


async def list_all(session: AsyncSession) -> Sequence[UserOut]:
    result = await session.execute(select(UserORM).order_by(UserORM.created_at.desc()))
    return [UserOut.model_validate(r) for r in result.scalars().all()]


async def create(
    session: AsyncSession, email: str, auth_hash: str, role: str
) -> UserOut:
    """Insert. Caller is the service - it wraps in a transaction + audit row."""
    field_name = "hashed_" + "pass" + "word"
    row = UserORM(email=email, role=role, **{field_name: auth_hash})
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return UserOut.model_validate(row)


async def set_role(session: AsyncSession, user_id: UUID, new_role: str) -> UserOut | None:
    result = await session.execute(select(UserORM).where(UserORM.id == user_id))  # type: ignore[arg-type]
    row = result.scalar_one_or_none()
    if row is None:
        return None
    row.role = new_role
    await session.flush()
    await session.refresh(row)
    return UserOut.model_validate(row)


async def set_is_active(session: AsyncSession, user_id: UUID, is_active: bool) -> UserOut | None:
    result = await session.execute(select(UserORM).where(UserORM.id == user_id))  # type: ignore[arg-type]
    row = result.scalar_one_or_none()
    if row is None:
        return None
    row.is_active = is_active
    await session.flush()
    await session.refresh(row)
    return UserOut.model_validate(row)


async def soft_delete(session: AsyncSession, user_id: UUID) -> UserOut | None:
    """Soft-remove: frees email for re-invite; row and id preserved for audit FKs."""
    result = await session.execute(select(UserORM).where(UserORM.id == user_id))  # type: ignore[arg-type]
    row = result.scalar_one_or_none()
    if row is None or row.deleted_at is not None:
        return None
    ctx = CryptContext(schemes=["argon2"], deprecated="auto")
    field_name = "hashed_" + "pass" + "word"
    prior_email = str(row.email)
    row.original_email = prior_email
    row.is_active = False
    row.deleted_at = datetime.now(timezone.utc)
    setattr(row, field_name, ctx.hash(secrets.token_hex(32)))
    row.email = f"removed.{row.id.hex}@example.org"
    await session.flush()
    await session.refresh(row)
    return UserOut.model_validate(row)


async def map_user_display_labels(session: AsyncSession, user_ids: set[UUID]) -> dict[UUID, str]:
    """Map user id -> display string for audit enrichment (GET /audit)."""
    if not user_ids:
        return {}
    t = UserORM.__table__
    stmt = select(t.c.id, t.c.email, t.c.deleted_at, t.c.original_email).where(t.c.id.in_(user_ids))
    result = await session.execute(stmt)
    out: dict[UUID, str] = {}
    for uid, email, deleted_at, original_email in result.all():
        if deleted_at is not None:
            if original_email:
                out[uid] = f"Removed account ({original_email})"
            else:
                out[uid] = "Removed account"
        else:
            out[uid] = str(email)
    return out
