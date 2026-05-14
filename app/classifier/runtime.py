"""Runtime classifier interface used by workers.

This module keeps the worker import stable while delegating to the real
ConvNeXt inference implementation.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from app.classifier.classify import (
    Prediction,
)
from app.classifier.classify import (
    classify as classify_impl,
)
from app.classifier.classify import (
    make_overlay as make_overlay_impl,
)

__all__ = ["Prediction", "classify", "make_overlay"]

_WEIGHTS_FILE = Path(__file__).resolve().parent / "models" / "classifier.pt"


class PredictionResult(BaseModel):
    label: str
    top1_confidence: float
    top5: list[dict[str, float | str]]


def classify(image_bytes: bytes) -> PredictionResult:
    """Run ConvNeXt inference (`classify.py`) and adapt to the `PredictionResult` jobs expect."""
    if not _WEIGHTS_FILE.is_file():
        raise FileNotFoundError(
            f"Missing classifier weights at {_WEIGHTS_FILE}. "
            "Ensure `app/classifier/models/classifier.pt` is present."
        )
    head = _WEIGHTS_FILE.read_bytes()[:80].lstrip()
    if head.startswith(b"version https://git-lfs"):
        raise RuntimeError(
            f"Classifier weights at {_WEIGHTS_FILE} are a Git LFS pointer, not PyTorch bytes. "
            "Run `git lfs pull` in the repo (or copy a real classifier.pt) before inference."
        )

    raw = classify_impl(image_bytes)
    top5_dicts: list[dict[str, float | str]] = [
        {"label": lbl, "confidence": float(score)} for lbl, score in raw.top5
    ]
    return PredictionResult(
        label=raw.label,
        top1_confidence=raw.top1_confidence,
        top5=top5_dicts,
    )


def make_overlay(
    *,
    image_bytes: bytes,
    prediction: PredictionResult,
) -> bytes:
    """Delegate to `classify.make_overlay`, adapting `PredictionResult` → `Prediction`."""

    top5_tuples: list[tuple[str, float]] = [
        (str(d["label"]), float(d["confidence"])) for d in prediction.top5
    ]
    pred = Prediction(
        label=prediction.label,
        top1_confidence=prediction.top1_confidence,
        top5=top5_tuples,
        scores={},
    )
    return make_overlay_impl(image_bytes, pred)
