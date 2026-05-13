"""Batch service. Owns cache invalidation per CACHE-04."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

import structlog
from fastapi_cache import FastAPICache
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import BatchOut, PredictionOut
from app.repositories import batch_repository, prediction_repository

logger = structlog.get_logger(__name__)


class BatchNotFound(Exception):
    pass


async def list_batches(
    session: AsyncSession, offset: int = 0, limit: int = 50
) -> Sequence[BatchOut]:
    return await batch_repository.list_paginated(session, offset=offset, limit=limit)


async def get_batch(
    session: AsyncSession, batch_id: UUID
) -> tuple[BatchOut, Sequence[PredictionOut]]:
    batch = await batch_repository.get_by_id(session, batch_id)
    if batch is None:
        raise BatchNotFound(str(batch_id))
    preds = await prediction_repository.list_for_batch(session, batch_id)
    return batch, preds


async def transition_state(session: AsyncSession, batch_id: UUID, state: str) -> BatchOut:
    """Atomic state transition. Worker uses this via prediction_service."""
    async with session.begin():
        updated = await batch_repository.set_state(session, batch_id, state)
        if updated is None:
            raise BatchNotFound(str(batch_id))
    await invalidate_batch_caches(batch_id)
    return updated


async def invalidate_batch_caches(batch_id: UUID) -> None:
    """Clear /batches list + /batches/{bid} detail caches (CACHE-04)."""
    await FastAPICache.clear(namespace="batches-list")
    await FastAPICache.clear(namespace=f"batches-detail:{batch_id}")
    logger.info("batch_cache_invalidated", batch_id=str(batch_id))
