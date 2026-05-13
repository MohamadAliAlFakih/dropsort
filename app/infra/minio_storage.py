from __future__ import annotations

from io import BytesIO

from minio import Minio

from app.core.config import get_settings


class MinioStorage:
    """Small MinIO adapter used by the ingestion and inference workers."""

    def __init__(self) -> None:
        settings = get_settings()

        self.bucket_name = settings.minio_bucket
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_bytes(
        self,
        *,
        object_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        self.ensure_bucket()

        self.client.put_object(
            bucket_name=self.bucket_name,
            object_name=object_key,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def download_bytes(self, *, object_key: str) -> bytes:
        response = self.client.get_object(self.bucket_name, object_key)

        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()


# minio_storage.py is an infrastructure adapter.
# It hides MinIO details behind simple methods like upload_bytes() and download_bytes(). 
# My workers use it to save incoming TIFFs, failed files, and overlay PNGs.