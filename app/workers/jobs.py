"""RQ inference job — second half of the SFTP -> classify -> store pipeline.

Pulls the image from MinIO, runs Saleh's classifier, generates overlay, uploads it,
then calls the service layer to write the prediction row + audit + cache invalidation.

`run_classification_job` is the RQ entrypoint. RQ calls it synchronously; we bridge
to the async service layer with `asyncio.run`. Idempotency is handled by the service
(UNIQUE on `content_sha256`).
"""

from __future__ import annotations

import asyncio

import structlog

from app.classifier.classify import classify, make_overlay
from app.core.logging import get_logger
from app.domain import TopKItem
from app.infra.minio_storage import MinioStorage
from app.services.prediction_service import record_prediction
from app.workers.db import get_worker_sessionmaker


def run_classification_job(
    *,
    batch_id: str,
    filename: str,
    object_key: str,
    content_sha256: str,
    request_id: str,
) -> None:
    """Synchronous RQ entrypoint. Bridges to async service via asyncio.run."""
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        batch_id=batch_id,
        filename=filename,
    )

    logger = get_logger(__name__)
    storage = MinioStorage()

    logger.info(
        "classification_job_started",
        object_key=object_key,
        content_sha256=content_sha256,
    )

    image_bytes = storage.download_bytes(object_key=object_key)
    prediction = classify(image_bytes)

    overlay_png_bytes = make_overlay(
        image_bytes=image_bytes,
        prediction=prediction,
    )

    overlay_object_key = f"overlays/{batch_id}/{filename}.png"
    storage.upload_bytes(
        object_key=overlay_object_key,
        data=overlay_png_bytes,
        content_type="image/png",
    )

    # Saleh's `classify` returns top5 as `list[dict]` (from runtime.py) or
    # `list[tuple[str, float]]` (from classify.py). Normalise to TopKItem.
    top5_items = _normalise_top5(prediction.top5)

    asyncio.run(
        _persist_prediction(
            batch_external_id=batch_id,
            filename=filename,
            content_sha256=content_sha256,
            minio_input_key=object_key,
            minio_overlay_key=overlay_object_key,
            label=prediction.label,
            top1_confidence=prediction.top1_confidence,
            top5=top5_items,
        )
    )

    logger.info(
        "classification_job_completed",
        overlay_object_key=overlay_object_key,
        predicted_label=prediction.label,
        top1_confidence=prediction.top1_confidence,
    )


async def _persist_prediction(
    *,
    batch_external_id: str,
    filename: str,
    content_sha256: str,
    minio_input_key: str,
    minio_overlay_key: str,
    label: str,
    top1_confidence: float,
    top5: list[TopKItem],
) -> None:
    """Acquire a worker-local DB session, call the service, return."""
    sessionmaker = get_worker_sessionmaker()
    async with sessionmaker() as session:
        await record_prediction(
            session=session,
            batch_external_id=batch_external_id,
            filename=filename,
            content_sha256=content_sha256,
            minio_input_key=minio_input_key,
            minio_overlay_key=minio_overlay_key,
            label=label,
            top1_confidence=top1_confidence,
            top5=top5,
        )


def _normalise_top5(top5_raw: object) -> list[TopKItem]:
    """Accept Saleh's classifier output shape (list of tuples or list of dicts)
    and convert to the service contract `list[TopKItem]`."""
    items: list[TopKItem] = []
    if not isinstance(top5_raw, list):
        return items
    for entry in top5_raw[:5]:
        if isinstance(entry, tuple) and len(entry) == 2:
            label, score = entry
            items.append(TopKItem(label=str(label), score=float(score)))
        elif isinstance(entry, dict):
            label_val = entry.get("label", "")
            score_val = entry.get("confidence", entry.get("score", 0.0)) or 0.0
            items.append(TopKItem(label=str(label_val), score=float(score_val)))
    return items
