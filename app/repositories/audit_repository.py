"""Audit log repository - append-only."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog as AuditLogORM
from app.domain import AuditEntryOut


async def append(
    session: AsyncSession,
    *,
    actor_id: UUID,
    action: str,
    target_type: str,
    target_id: str,
    metadata: dict[str, Any] | None = None,
) -> AuditEntryOut:
    row = AuditLogORM(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_jsonb=metadata,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return AuditEntryOut.model_validate(row)


async def list_paginated(
    session: AsyncSession, offset: int = 0, limit: int = 50
) -> Sequence[AuditEntryOut]:
    stmt = (
        select(AuditLogORM)
        .order_by(AuditLogORM.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [AuditEntryOut.model_validate(r) for r in result.scalars().all()]
