from __future__ import annotations

from pydantic import BaseModel


class PredictionResult(BaseModel):
    label: str
    top1_confidence: float
    top5: list[dict[str, float | str]]


def classify(image_bytes: bytes) -> PredictionResult:
    """Temporary placeholder until the real ConvNeXt classifier is wired."""

    return PredictionResult(
        label="invoice",
        top1_confidence=0.91,
        top5=[
            {"label": "invoice", "confidence": 0.91},
            {"label": "form", "confidence": 0.04},
            {"label": "letter", "confidence": 0.02},
            {"label": "memo", "confidence": 0.02},
            {"label": "email", "confidence": 0.01},
        ],
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

# This is temporary. It simulates the classifier 
# so I can test the SFTP → MinIO → RQ → worker flow before the real ConvNeXt model is ready.
#  Later, Saleh replaces this with the actual model inference code.