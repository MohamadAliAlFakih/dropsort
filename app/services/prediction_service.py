"""Prediction service.

- `record_prediction` is the worker-import contract (PIPE-04 / CONTEXT D-11).
- `relabel` enforces the top1 < 0.7 guard.
- `list_recent` backs /predictions/recent.

All writes are transactional; cache invalidation post-commit (CACHE-04).
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

import structlog
from fastapi_cache import FastAPICache
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import PredictionOut, TopKItem
from app.repositories import audit_repository, batch_repository, prediction_repository

logger = structlog.get_logger(__name__)

RELABEL_CONFIDENCE_THRESHOLD = 0.7  # brief AUTH-05


class PredictionNotFound(Exception):
    pass


class RelabelNotAllowed(Exception):
    """Raised when top1_confidence >= RELABEL_CONFIDENCE_THRESHOLD.
    Router translates to HTTP 409 Conflict.
    """

    def __init__(self, pid: UUID, top1: float) -> None:
        self.pid = pid
        self.top1 = top1
        super().__init__(
            f"Relabel rejected: top1_confidence={top1:.4f} >= {RELABEL_CONFIDENCE_THRESHOLD}"
        )


async def list_recent(session: AsyncSession, limit: int = 50) -> Sequence[PredictionOut]:
    return await prediction_repository.list_recent(session, limit=limit)


async def relabel(
    *,
    session: AsyncSession,
    pid: UUID,
    new_label: str,
    actor_id: UUID,
) -> PredictionOut:
    """Reviewer relabels a prediction."""
    async with session.begin():
        current = await prediction_repository.get_by_id(session, pid)
        if current is None:
            raise PredictionNotFound(str(pid))
        if current.top1_confidence >= RELABEL_CONFIDENCE_THRESHOLD:
            raise RelabelNotAllowed(pid, current.top1_confidence)

        updated = await prediction_repository.relabel(session, pid, new_label, actor_id)
        if updated is None:
            raise PredictionNotFound(str(pid))

        await audit_repository.append(
            session,
            actor_id=actor_id,
            action="prediction_relabeled",
            target_type="prediction",
            target_id=str(pid),
            metadata={
                "from": current.label,
                "to": new_label,
                "top1_confidence": current.top1_confidence,
            },
        )

    await FastAPICache.clear(namespace=f"batches-detail:{updated.batch_id}")
    await FastAPICache.clear(namespace="predictions-recent")
    logger.info(
        "prediction_relabeled",
        prediction_id=str(pid),
        label_from=current.label,
        label_to=new_label,
    )
    return updated


# ---------------- Worker import contract (PIPE-04 / CONTEXT D-11) ----------------


async def record_prediction(
    *,
    session: AsyncSession,
    batch_external_id: str,
    filename: str,
    content_sha256: str,
    minio_input_key: str,
    minio_overlay_key: str | None,
    label: str,
    top1_confidence: float,
    top5: list[TopKItem],
) -> PredictionOut | None:
    """Worker entrypoint into the service layer.

    Atomic: upsert batch -> insert prediction (skip on UNIQUE) -> commit.
    Returns None on PIPE-05 idempotent skip. Invalidates caches post-commit.

    Phase 4 imports this directly:
        from app.services.prediction_service import record_prediction
    """
    async with session.begin():
        batch = await batch_repository.upsert_external(session, batch_external_id)
        created = await prediction_repository.create(
            session,
            batch_id=batch.id,
            filename=filename,
            content_sha256=content_sha256,
            minio_input_key=minio_input_key,
            minio_overlay_key=minio_overlay_key,
            label=label,
            top1_confidence=top1_confidence,
            top5=top5,
        )
        if created is None:
            logger.info(
                "prediction_skipped_duplicate",
                content_sha256=content_sha256,
                filename=filename,
            )
            return None

    await FastAPICache.clear(namespace="batches-list")
    await FastAPICache.clear(namespace=f"batches-detail:{batch.id}")
    await FastAPICache.clear(namespace="predictions-recent")
    logger.info(
        "prediction_recorded",
        prediction_id=str(created.id),
        batch_id=str(batch.id),
        filename=filename,
        label=label,
        top1_confidence=top1_confidence,
    )
    return created


async def mark_batch_failed(
    *,
    session: AsyncSession,
    batch_external_id: str,
    filename: str,
    reason: str,
) -> None:
    """Mark a batch as failed after PIPE-06 retries are exhausted.

    Atomic: upsert batch -> set state='failed' -> audit row -> commit.
    Invalidates batch caches post-commit.

    Phase 4 worker calls this from its exception handler when an RQ job's
    retry budget is exhausted.
    """
    from app.repositories import user_repository

    async with session.begin():
        # System actor: admin user (FK constraint requires a real user).
        # If admin lookup fails (shouldn't happen post-revision 0002), we still
        # mark the batch failed but skip the audit row rather than blow up.
        admin = await user_repository.get_by_email(session, "admin@example.com")

        batch = await batch_repository.upsert_external(session, batch_external_id)
        await batch_repository.set_state(session, batch.id, "failed")
        if admin is not None:
            await audit_repository.append(
                session,
                actor_id=admin.id,
                action="batch_state_changed",
                target_type="batch",
                target_id=str(batch.id),
                metadata={
                    "to": "failed",
                    "filename": filename,
                    "reason": reason[:500],
                    "system": True,
                },
            )

    await FastAPICache.clear(namespace="batches-list")
    await FastAPICache.clear(namespace=f"batches-detail:{batch.id}")
    logger.error(
        "batch_marked_failed",
        batch_id=str(batch.id),
        filename=filename,
        reason=reason[:200],
    )
