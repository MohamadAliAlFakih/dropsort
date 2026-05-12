from __future__ import annotations

import structlog

from app.core.logging import get_logger
from app.infra.minio_storage import MinioStorage

# Saleh should replace/provide this module.
from app.classifier.runtime import classify, make_overlay

# Fakih should replace/provide this service implementation.
from app.services.prediction_service import prediction_exists, record_prediction


def run_classification_job(
    *,
    batch_id: str,
    filename: str,
    object_key: str,
    content_sha256: str,
    request_id: str,
) -> None:
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

    if prediction_exists(
        batch_id=batch_id,
        filename=filename,
        content_sha256=content_sha256,
    ):
        logger.info("classification_job_idempotent_noop")
        return

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

    record_prediction(
        batch_id=batch_id,
        filename=filename,
        content_sha256=content_sha256,
        original_object_key=object_key,
        overlay_object_key=overlay_object_key,
        predicted_label=prediction.label,
        top1_confidence=prediction.top1_confidence,
        top5=prediction.top5,
        request_id=request_id,
    )

    logger.info(
        "classification_job_completed",
        overlay_object_key=overlay_object_key,
        predicted_label=prediction.label,
        top1_confidence=prediction.top1_confidence,
    )

# jobs.py contains the RQ job function. This is the second half of the pipeline. 
# It downloads the image from MinIO, runs classification, 
# creates an overlay, uploads the overlay, and records the prediction through the service layer.