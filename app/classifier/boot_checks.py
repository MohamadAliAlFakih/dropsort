"""Refuse-to-start checks for the classifier (BOOT-03, BOOT-04).

Called during API and worker lifespan before serving traffic / processing jobs.
Any failure raises RuntimeError so the process exits with a clear log line rather
than serving requests with a missing or corrupt model.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

_CLASSIFIER_DIR = Path(__file__).parent / "models"
_WEIGHTS_FILE = _CLASSIFIER_DIR / "classifier.pt"
_MODEL_CARD = _CLASSIFIER_DIR / "model_card.json"


class ClassifierBootError(RuntimeError):
    """Raised when a BOOT-03 or BOOT-04 check fails."""


def verify_classifier_present() -> None:
    """BOOT-03 part 1: classifier.pt + model_card.json must exist."""
    if not _WEIGHTS_FILE.is_file():
        raise ClassifierBootError(
            f"BOOT-03: classifier weights not found at {_WEIGHTS_FILE}. "
            "Run `git lfs pull` to fetch the LFS-tracked weights."
        )
    if not _MODEL_CARD.is_file():
        raise ClassifierBootError(
            f"BOOT-03: model_card.json not found at {_MODEL_CARD}."
        )


def verify_classifier_sha() -> None:
    """BOOT-03 part 2: SHA-256 of classifier.pt must match `weights_sha256`
    in model_card.json. Detects corrupt or tampered weight files."""
    expected = _read_model_card().get("weights_sha256")
    if not expected:
        raise ClassifierBootError(
            "BOOT-03: model_card.json has no `weights_sha256` field."
        )

    actual = _sha256_of(_WEIGHTS_FILE)
    if actual != expected:
        raise ClassifierBootError(
            f"BOOT-03: classifier.pt SHA-256 mismatch. "
            f"Expected {expected[:16]}..., got {actual[:16]}..."
        )


def verify_classifier_top1_above_threshold() -> None:
    """BOOT-04: model_card.json `test_top1` must be >= MIN_MODEL_TOP1 env var.
    Defends against accidentally shipping a regressed model."""
    threshold_raw = os.environ.get("MIN_MODEL_TOP1")
    if not threshold_raw:
        # No threshold set -> skip (Phase 2 sets this post-Colab eval; if absent
        # in dev we still want the API to come up). Brief makes the threshold a
        # README-declared knob, not always-on.
        return
    try:
        threshold = float(threshold_raw)
    except ValueError as exc:
        raise ClassifierBootError(
            f"BOOT-04: MIN_MODEL_TOP1 is not a number: {threshold_raw!r}"
        ) from exc

    card = _read_model_card()
    # model_card structure: { "metrics": { "test_top1": 0.79, ... }, ... }
    test_top1 = (card.get("metrics") or {}).get("test_top1")
    if test_top1 is None:
        raise ClassifierBootError(
            "BOOT-04: model_card.json has no `metrics.test_top1` field."
        )

    if float(test_top1) < threshold:
        raise ClassifierBootError(
            f"BOOT-04: model test_top1={test_top1} is below "
            f"MIN_MODEL_TOP1={threshold}. Refusing to boot."
        )


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_model_card() -> dict:
    with _MODEL_CARD.open(encoding="utf-8") as fh:
        return json.load(fh)
