"""Batch repository."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Batch as BatchORM
from app.db.models import Prediction as PredictionORM
from app.domain import BatchOut


async def list_paginated(
    session: AsyncSession, offset: int = 0, limit: int = 50
) -> Sequence[BatchOut]:
    pred_count = (
        select(PredictionORM.batch_id, func.count().label("n"))
        .group_by(PredictionORM.batch_id)
        .subquery()
    )
    stmt = (
        select(BatchORM, func.coalesce(pred_count.c.n, 0))
        .outerjoin(pred_count, BatchORM.id == pred_count.c.batch_id)
        .order_by(BatchORM.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    out: list[BatchOut] = []
    for batch, count in result.all():
        bo = BatchOut.model_validate(batch)
        bo.prediction_count = int(count)
        out.append(bo)
    return out


async def get_by_id(session: AsyncSession, batch_id: UUID) -> BatchOut | None:
    result = await session.execute(select(BatchORM).where(BatchORM.id == batch_id))
    row = result.scalar_one_or_none()
    return BatchOut.model_validate(row) if row else None


async def upsert_external(session: AsyncSession, external_id: str) -> BatchOut:
    """Get-or-create by external_id. Worker calls this when first file in a batch lands."""
    result = await session.execute(
        select(BatchORM).where(BatchORM.external_id == external_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = BatchORM(external_id=external_id, state="received")
        session.add(row)
        await session.flush()
        await session.refresh(row)
    return BatchOut.model_validate(row)


async def set_state(session: AsyncSession, batch_id: UUID, state: str) -> BatchOut | None:
    result = await session.execute(select(BatchORM).where(BatchORM.id == batch_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    row.state = state
    await session.flush()
    await session.refresh(row)
    return BatchOut.model_validate(row)
