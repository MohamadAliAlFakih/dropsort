"""Runtime classifier interface used by workers.

This module keeps the worker import stable while delegating to the real
ConvNeXt inference implementation.
"""

from __future__ import annotations

from app.classifier.classify import Prediction, classify, make_overlay

__all__ = ["Prediction", "classify", "make_overlay"]