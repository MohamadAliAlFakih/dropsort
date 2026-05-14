from __future__ import annotations

import time
from uuid import uuid4

import structlog

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infra.minio_storage import MinioStorage
from app.infra.queue import QueueClient
from app.infra.sftp_client import SftpClient
from app.pipeline.tiff_ingest import calculate_sha256, validate_tiff


def new_request_id() -> str:
    return str(uuid4())


def new_batch_id() -> str:
    return str(uuid4())


def ingest_once(
    *,
    sftp: SftpClient,
    storage: MinioStorage,
    queue: QueueClient,
) -> None:
    logger = get_logger(__name__)

    filenames = sftp.list_files()

    for filename in filenames:
        request_id = new_request_id()
        batch_id = new_batch_id()

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            batch_id=batch_id,
            filename=filename,
        )

        try:
            logger.info("sftp_file_detected")

            file_bytes = sftp.read_file(filename=filename)
            content_sha256 = calculate_sha256(file_bytes)

            is_valid, reason = validate_tiff(filename, file_bytes)

            if not is_valid:
                failed_key = f"failed/{batch_id}/{filename}"

                storage.upload_bytes(
                    object_key=failed_key,
                    data=file_bytes,
                    content_type="application/octet-stream",
                )

                logger.warning(
                    "malformed_input_quarantined",
                    reason=reason,
                    object_key=failed_key,
                )

                sftp.delete_file(filename=filename)
                continue

            object_key = f"incoming/{batch_id}/{filename}"

            storage.upload_bytes(
                object_key=object_key,
                data=file_bytes,
                content_type="image/tiff",
            )

            job_id = queue.enqueue_classification_job(
                batch_id=batch_id,
                filename=filename,
                object_key=object_key,
                content_sha256=content_sha256,
                request_id=request_id,
            )

            logger.info(
                "classification_job_enqueued",
                object_key=object_key,
                content_sha256=content_sha256,
                job_id=job_id,
            )

            sftp.delete_file(filename=filename)

        except Exception:
            logger.exception("sftp_ingest_failed")


def main() -> None:
    configure_logging()

    logger = get_logger(__name__)
    settings = get_settings()

    sftp = SftpClient()
    storage = MinioStorage()
    queue = QueueClient()

    logger.info(
        "sftp_ingest_started",
        poll_interval_seconds=settings.sftp_poll_interval_seconds,
    )

    while True:
        ingest_once(sftp=sftp, storage=storage, queue=queue)
        time.sleep(settings.sftp_poll_interval_seconds)


if __name__ == "__main__":
    main()

# sftp_ingest.py is the first pipeline worker. It watches the scanner SFTP folder.
# Valid TIFFs go to MinIO under incoming/ and become RQ jobs.
# Invalid files go to MinIO under failed/ and no prediction job is created.
