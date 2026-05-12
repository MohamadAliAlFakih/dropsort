from __future__ import annotations

from app.core.logging import get_logger


def prediction_exists(
    *,
    batch_id: str,
    filename: str,
    content_sha256: str,
) -> bool:
    """Temporary placeholder.

    Final version should check the DB using the repository layer and enforce
    UNIQUE(batch_id, filename, content_sha256).
    """

    return False


def record_prediction(
    *,
    batch_id: str,
    filename: str,
    content_sha256: str,
    original_object_key: str,
    overlay_object_key: str,
    predicted_label: str,
    top1_confidence: float,
    top5: list[dict],
    request_id: str,
) -> None:
    """Temporary placeholder.

    Final version must:
    1. Insert prediction row through repository.
    2. Write audit log.
    3. Invalidate affected Redis caches.
    """

    logger = get_logger(__name__)

    logger.info(
        "prediction_record_placeholder_called",
        batch_id=batch_id,
        filename=filename,
        content_sha256=content_sha256,
        original_object_key=original_object_key,
        overlay_object_key=overlay_object_key,
        predicted_label=predicted_label,
        top1_confidence=top1_confidence,
        top5=top5,
        request_id=request_id,
    )


def mark_batch_failed(
    *,
    batch_id: str,
    filename: str,
    reason: str,
    request_id: str,
) -> None:
    """Temporary placeholder.

    Final version should mark batch/job failed, write audit row, and invalidate caches.
    """

    logger = get_logger(__name__)

    logger.error(
        "batch_failed_placeholder_called",
        batch_id=batch_id,
        filename=filename,
        reason=reason,
        request_id=request_id,
    )

# prediction_service.py is the service boundary between my worker and the database.
#  My worker calls this service instead of inserting directly into SQL.
#  The final version will handle prediction creation, audit logging,
#  idempotency, and cache invalidation.    