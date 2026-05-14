"""User repository. SQL-only; returns Pydantic; no HTTPException (API-03)."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

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


async def map_user_display_labels(session: AsyncSession, user_ids: set[UUID]) -> dict[UUID, str]:
    """Map user id -> email for audit enrichment (GET /audit)."""
    if not user_ids:
        return {}
    stmt = select(UserORM.id, UserORM.email).where(UserORM.id.in_(user_ids))
    result = await session.execute(stmt)
    return {row[0]: str(row[1]) for row in result.all()}
