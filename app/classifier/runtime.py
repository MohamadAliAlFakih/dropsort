"""Runtime classifier interface used by workers.

This module keeps the worker import stable while delegating to the real
ConvNeXt inference implementation.
"""

from __future__ import annotations

from app.classifier.classify import Prediction, classify, make_overlay

__all__ = ["Prediction", "classify", "make_overlay"]
from pathlib import Path

from pydantic import BaseModel

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

    from app.classifier.classify import classify as convnext_classify

    raw = convnext_classify(image_bytes)
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
    """Temporary placeholder until the real overlay generator is wired."""

    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01"
        b"\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00"
        b"\x90wS\xde"
        b"\x00\x00\x00\x0cIDAT"
        b"\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xe2&\xb0"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
