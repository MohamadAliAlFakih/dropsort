"""Golden-set replay test.

Loads golden_expected.json, runs classify() over every image in golden_images/,
and asserts:
  - pred_label matches expected (byte-identical string comparison)
  - top1_confidence is within 1e-6 of expected

CI invokes this directly: `python -m pytest app/classifier/eval/golden.py`
or `python app/classifier/eval/golden.py` for a standalone run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_EVAL_DIR = Path(__file__).parent
_IMAGES_DIR = _EVAL_DIR / "golden_images"
_EXPECTED_FILE = _EVAL_DIR / "golden_expected.json"

_TOP1_TOLERANCE = 1e-6


def run_golden_checks() -> None:
    expected_entries: list[dict] = json.loads(_EXPECTED_FILE.read_text(encoding="utf-8"))

    # import here so the module is importable without torch when only the
    # test harness is collecting; actual execution requires torch.
    from app.classifier.classify import classify

    failures: list[str] = []

    for entry in expected_entries:
        filename: str = entry["filename"]
        expected_label: str = entry["pred_label"]
        expected_conf: float = entry["top1_confidence"]

        image_path = _IMAGES_DIR / filename
        if not image_path.exists():
            failures.append(f"MISSING image: {filename}")
            continue

        image_bytes = image_path.read_bytes()
        prediction = classify(image_bytes)

        if prediction.label != expected_label:
            failures.append(
                f"LABEL MISMATCH {filename}: "
                f"expected={expected_label!r}  got={prediction.label!r}"
            )

        conf_delta = abs(prediction.top1_confidence - expected_conf)
        if conf_delta > _TOP1_TOLERANCE:
            failures.append(
                f"CONFIDENCE DRIFT {filename}: "
                f"expected={expected_conf}  got={prediction.top1_confidence}  "
                f"delta={conf_delta:.2e} > {_TOP1_TOLERANCE}"
            )

    if failures:
        msg = "\n".join(["Golden-set replay FAILED:"] + failures)
        raise AssertionError(msg)

    print(f"Golden-set replay PASSED ({len(expected_entries)} images).")


# ── pytest entry point ────────────────────────────────────────────────────────

def test_golden_replay() -> None:
    """pytest-discoverable wrapper around run_golden_checks."""
    run_golden_checks()


# ── standalone entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        run_golden_checks()
    except AssertionError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
