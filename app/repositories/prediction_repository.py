"""Prediction repository - content_sha256 unique key supports PIPE-05 idempotency."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Prediction as PredictionORM
from app.domain import PredictionOut, TopKItem


async def list_recent(session: AsyncSession, limit: int = 50) -> Sequence[PredictionOut]:
    stmt = select(PredictionORM).order_by(PredictionORM.created_at.desc()).limit(limit)
    result = await session.execute(stmt)
    return [_to_out(r) for r in result.scalars().all()]


async def list_for_batch(session: AsyncSession, batch_id: UUID) -> Sequence[PredictionOut]:
    stmt = (
        select(PredictionORM)
        .where(PredictionORM.batch_id == batch_id)
        .order_by(PredictionORM.created_at.asc())
    )
    result = await session.execute(stmt)
    return [_to_out(r) for r in result.scalars().all()]


async def get_by_id(session: AsyncSession, pid: UUID) -> PredictionOut | None:
    result = await session.execute(select(PredictionORM).where(PredictionORM.id == pid))
    row = result.scalar_one_or_none()
    return _to_out(row) if row else None


async def map_id_to_filename(session: AsyncSession, prediction_ids: set[UUID]) -> dict[UUID, str]:
    if not prediction_ids:
        return {}
    stmt = select(PredictionORM.id, PredictionORM.filename).where(
        PredictionORM.id.in_(prediction_ids)
    )
    result = await session.execute(stmt)
    return {row[0]: row[1] for row in result.all()}


async def create(
    session: AsyncSession,
    *,
    batch_id: UUID,
    filename: str,
    content_sha256: str,
    minio_input_key: str,
    minio_overlay_key: str | None,
    label: str,
    top1_confidence: float,
    top5: list[TopKItem],
) -> PredictionOut | None:
    """Insert. Returns None on UNIQUE violation (PIPE-05 idempotency)."""
    row = PredictionORM(
        batch_id=batch_id,
        filename=filename,
        content_sha256=content_sha256,
        minio_input_key=minio_input_key,
        minio_overlay_key=minio_overlay_key,
        label=label,
        top1_confidence=top1_confidence,
        top5_json=[item.model_dump() for item in top5],
    )
    session.add(row)
    try:
        await session.flush()
        await session.refresh(row)
    except IntegrityError:
        await session.rollback()
        return None
    return _to_out(row)


async def relabel(
    session: AsyncSession, pid: UUID, new_label: str, actor_id: UUID
) -> PredictionOut | None:
    result = await session.execute(select(PredictionORM).where(PredictionORM.id == pid))
    row = result.scalar_one_or_none()
    if row is None:
        return None
    row.relabel_label = new_label
    row.relabel_actor_id = actor_id
    row.relabel_at = datetime.now(tz=timezone.utc)
    await session.flush()
    await session.refresh(row)
    return _to_out(row)


def _to_out(row: PredictionORM) -> PredictionOut:
    return PredictionOut(
        id=row.id,
        batch_id=row.batch_id,
        filename=row.filename,
        label=row.label,
        top1_confidence=row.top1_confidence,
        top5=[TopKItem(**item) for item in row.top5_json],
        minio_overlay_key=row.minio_overlay_key,
        relabel_label=row.relabel_label,
        relabel_actor_id=row.relabel_actor_id,
        relabel_at=row.relabel_at,
        created_at=row.created_at,
    )
