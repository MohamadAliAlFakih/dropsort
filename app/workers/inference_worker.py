from __future__ import annotations

import asyncio
import sys
from typing import Any

import structlog
from redis import Redis
from rq import Queue, Worker
from rq.job import Job

from app.classifier.boot_checks import (
    verify_classifier_present,
    verify_classifier_sha,
    verify_classifier_top1_above_threshold,
)
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.services.prediction_service import mark_batch_failed
from app.workers.db import get_worker_sessionmaker


def run_boot_checks() -> None:
    verify_classifier_present()
    verify_classifier_sha()
    verify_classifier_top1_above_threshold()


async def _mark_batch_failed_async(
    *,
    batch_external_id: str,
    filename: str,
    reason: str,
) -> None:
    sessionmaker = get_worker_sessionmaker()
    async with sessionmaker() as session:
        await mark_batch_failed(
            session=session,
            batch_external_id=batch_external_id,
            filename=filename,
            reason=reason,
        )


def handle_worker_exception(
    job: Job,
    exc_type: type[BaseException],
    exc_value: BaseException,
    traceback: Any,
) -> bool:
    kwargs = job.kwargs or {}

    request_id = kwargs.get("request_id")
    batch_id = kwargs.get("batch_id")
    filename = kwargs.get("filename")

    if request_id:
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            batch_id=batch_id,
            filename=filename,
        )

    logger = get_logger(__name__)

    retries_left = getattr(job, "retries_left", 0)

    logger.error(
        "classification_job_failed_attempt",
        job_id=job.id,
        retries_left=retries_left,
        error_type=exc_type.__name__,
        error=str(exc_value),
    )

    if retries_left and retries_left > 0:
        return True

    if batch_id and filename:
        asyncio.run(
            _mark_batch_failed_async(
                batch_external_id=batch_id,
                filename=filename,
                reason=str(exc_value),
            )
        )

        logger.error(
            "classification_job_permanently_failed",
            job_id=job.id,
        )

    return True


def main() -> None:
    configure_logging()

    logger = get_logger(__name__)

    try:
        run_boot_checks()
    except Exception:
        logger.exception("worker_refused_to_start_classifier_boot_check_failed")
        sys.exit(1)

    settings = get_settings()

    redis = Redis.from_url(settings.redis_url)
    queue = Queue(settings.rq_queue_name, connection=redis)

    worker = Worker(
        [queue],
        connection=redis,
        exception_handlers=[handle_worker_exception],
    )

    logger.info("inference_worker_started", queue_name=settings.rq_queue_name)

    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()

# inference_worker.py is the entrypoint for the worker container.
#     It first checks that the classifier model is valid.
# If the model is missing, hash is wrong, or accuracy is below threshold, 
# the worker refuses to start. If checks pass, it starts listening to the RQ queue.