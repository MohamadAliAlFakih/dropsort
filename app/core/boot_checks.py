"""Startup checks for the classifier weights (BOOT-04).

Called during the FastAPI lifespan before the server accepts traffic.
Raises RuntimeError on any failure so the process exits immediately
rather than serving requests with a missing or corrupt model.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_MODEL_DIR = Path(__file__).parent.parent / "classifier" / "models"
_WEIGHTS_FILE = _MODEL_DIR / "classifier.pt"
_MODEL_CARD = _MODEL_DIR / "model_card.json"


def verify_classifier_present() -> None:
    """Raise RuntimeError if classifier.pt does not exist on disk."""
    if not _WEIGHTS_FILE.exists():
        raise RuntimeError(
            f"Classifier weights not found at {_WEIGHTS_FILE}. "
            "Ensure classifier.pt is present (downloaded from Git LFS) before starting."
        )


def verify_classifier_sha() -> None:
    """Raise RuntimeError if SHA-256 of classifier.pt does not match model_card.json."""
    if not _MODEL_CARD.exists():
        raise RuntimeError(f"model_card.json not found at {_MODEL_CARD}.")

    card = json.loads(_MODEL_CARD.read_text(encoding="utf-8"))
    expected_sha: str = card["weights_sha256"]

    sha = hashlib.sha256()
    with _WEIGHTS_FILE.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            sha.update(chunk)
    actual_sha = sha.hexdigest()

    if actual_sha != expected_sha:
        raise RuntimeError(
            f"classifier.pt SHA-256 mismatch.\n"
            f"  expected: {expected_sha}\n"
            f"  actual:   {actual_sha}\n"
            "The weights file may be corrupt or replaced. Re-pull from Git LFS."
        )


def verify_classifier_top1_above_threshold(min_top1: float) -> None:
    """Raise RuntimeError if the model card's test_top1 is below min_top1.

    This enforces the BOOT-04 refuse-to-start rule: a model that regressed
    below the threshold should not serve traffic.
    """
    if not _MODEL_CARD.exists():
        raise RuntimeError(f"model_card.json not found at {_MODEL_CARD}.")

    card = json.loads(_MODEL_CARD.read_text(encoding="utf-8"))
    actual_top1: float = card["metrics"]["test_top1"]

    if actual_top1 < min_top1:
        raise RuntimeError(
            f"Classifier test_top1 {actual_top1:.4f} is below the required threshold "
            f"{min_top1:.4f}. Update or retrain the model before starting the service."
        )
