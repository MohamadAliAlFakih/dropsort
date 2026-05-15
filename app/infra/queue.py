from __future__ import annotations

from redis import Redis
from rq import Queue, Retry

from app.core.config import get_settings


class QueueClient:
    """RQ queue adapter for classification jobs."""

    def __init__(self) -> None:
        settings = get_settings()

        self.redis = Redis.from_url(settings.redis_url)
        self.queue = Queue(settings.rq_queue_name, connection=self.redis)

    def enqueue_classification_job(
        self,
        *,
        batch_id: str,
        filename: str,
        object_key: str,
        content_sha256: str,
        request_id: str,
    ) -> str:
        job = self.queue.enqueue(
             "app.workers.jobs.run_classification_job",
            batch_id=batch_id,
            filename=filename,
            object_key=object_key,
            content_sha256=content_sha256,
            request_id=request_id,
            retry=Retry(max=3, interval=[1, 5, 15]),
            job_timeout=60,
        )

        return job.id
    
# queue.py wraps Redis Queue. The ingestion worker uses it to enqueue classification jobs.
# Each job carries batch_id, filename, object_key, content_sha256, 
# and request_id, so the inference worker has everything it needs.