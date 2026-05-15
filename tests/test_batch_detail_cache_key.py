"""Batch detail cache key must align with FastAPICache.clear (CACHE-04)."""

from __future__ import annotations

from uuid import UUID

from app.api.batches import _batch_detail_key_builder


def test_batch_detail_cache_key_matches_fastapi_clear_pattern() -> None:
    """Clear uses KEYS dropsort-cache:batches-detail:<uuid>:* — key must extend that prefix."""
    prefix_namespace = "dropsort-cache:batches-detail"
    bid = UUID("00000000-0000-0000-0000-000000000042")
    key = _batch_detail_key_builder(
        None, prefix_namespace, kwargs={"batch_id": bid}
    )
    assert key == f"{prefix_namespace}:{bid}:detail"
    assert key.startswith("dropsort-cache:batches-detail:")
    assert key.endswith(":detail")
