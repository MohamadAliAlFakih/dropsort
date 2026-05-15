"""TIFF validation shared by SFTP ingest and browser upload (same rules as PIPE-01)."""

from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings

SUPPORTED_EXTENSIONS = {".tif", ".tiff"}


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_tiff(filename: str, data: bytes) -> tuple[bool, str | None]:
    settings = get_settings()

    max_bytes = settings.pipeline_max_file_size_mb * 1024 * 1024
    extension = Path(filename).suffix.lower()

    if len(data) == 0:
        return False, "zero_byte_file"

    if len(data) > max_bytes:
        return False, "file_too_large"

    if extension not in SUPPORTED_EXTENSIONS:
        return False, "unsupported_extension"

    try:
        image = Image.open(BytesIO(data))
        image.verify()
    except UnidentifiedImageError:
        return False, "not_an_image"
    except Exception:
        return False, "image_validation_failed"

    return True, None
