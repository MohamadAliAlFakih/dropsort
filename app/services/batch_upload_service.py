"""Browser TIFF upload → MinIO `incoming/*` + RQ (same contract as `sftp_ingest`)."""

from __future__ import annotations

import asyncio
import uuid
from pathlib import PurePath

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import BatchOut
from app.infra.minio_storage import MinioStorage
from app.infra.queue import QueueClient
from app.pipeline.tiff_ingest import calculate_sha256, validate_tiff
from app.repositories import batch_repository
from app.services.batch_service import invalidate_batch_caches

logger = structlog.get_logger(__name__)


class UploadRejected(Exception):
    """Invalid TIFF; `reason` matches SFTP quarantine codes (e.g. `unsupported_extension`)."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _safe_filename(raw: str | None) -> str:
    if not raw:
        raise UploadRejected("missing_filename")
    name = PurePath(raw).name
    if not name or name in (".", ".."):
        raise UploadRejected("invalid_filename")
    if "/" in raw or "\\" in raw:
        raise UploadRejected("invalid_filename")
    return name


def _upload_bytes_sync(*, object_key: str, data: bytes, content_type: str) -> None:
    storage = MinioStorage()
    storage.upload_bytes(object_key=object_key, data=data, content_type=content_type)


def _enqueue_sync(
    *,
    batch_external_id: str,
    filename: str,
    object_key: str,
    content_sha256: str,
    request_id: str,
) -> str:
    queue = QueueClient()
    return queue.enqueue_classification_job(
        batch_id=batch_external_id,
        filename=filename,
        object_key=object_key,
        content_sha256=content_sha256,
        request_id=request_id,
    )


async def enqueue_browser_tiff(
    session: AsyncSession,
    *,
    file_bytes: bytes,
    filename: str,
) -> tuple[BatchOut, str]:
    safe_name = _safe_filename(filename)
    is_valid, reason = validate_tiff(safe_name, file_bytes)
    if not is_valid:
        q_batch = str(uuid.uuid4())
        failed_key = f"failed/{q_batch}/{safe_name}"
        await asyncio.to_thread(
            _upload_bytes_sync,
            object_key=failed_key,
            data=file_bytes,
            content_type="application/octet-stream",
        )
        logger.warning("browser_upload_rejected", reason=reason, object_key=failed_key)
        raise UploadRejected(reason or "validation_failed")

    external_id = str(uuid.uuid4())
    content_sha256 = calculate_sha256(file_bytes)
    object_key = f"incoming/{external_id}/{safe_name}"
    request_id = str(uuid.uuid4())

    await asyncio.to_thread(
        _upload_bytes_sync,
        object_key=object_key,
        data=file_bytes,
        content_type="image/tiff",
    )

    async with session.begin():
        batch = await batch_repository.upsert_external(session, external_id)

    job_id = await asyncio.to_thread(
        _enqueue_sync,
        batch_external_id=external_id,
        filename=safe_name,
        object_key=object_key,
        content_sha256=content_sha256,
        request_id=request_id,
    )

    await invalidate_batch_caches(batch.id)
    logger.info(
        "browser_upload_enqueued",
        batch_id=str(batch.id),
        external_id=external_id,
        job_id=job_id,
        object_key=object_key,
    )
    return batch, job_id
