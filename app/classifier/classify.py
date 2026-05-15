"""ConvNeXt Tiny inference — the only place that touches the .pt weights."""

from __future__ import annotations

import io
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import torch
import torchvision.transforms as T
from PIL import Image, ImageDraw, ImageFont
from torchvision.models import convnext_tiny

_MODEL_DIR = Path(__file__).parent / "models"
_WEIGHTS_FILE = _MODEL_DIR / "classifier.pt"

_CLASS_NAMES: list[str] = [
    "letter",
    "form",
    "email",
    "handwritten",
    "advertisement",
    "scientific_report",
    "scientific_publication",
    "specification",
    "file_folder",
    "news_article",
    "budget",
    "invoice",
    "presentation",
    "questionnaire",
    "resume",
    "memo",
]

_TRANSFORM = T.Compose(
    [
        T.Resize(256),
        T.CenterCrop(224),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


@dataclass(frozen=True)
class Prediction:
    label: str
    top1_confidence: float
    top5: list[tuple[str, float]]
    scores: dict[str, float]


@lru_cache(maxsize=1)
def _load_model() -> torch.nn.Module:
    model = convnext_tiny(weights=None, num_classes=len(_CLASS_NAMES))
    state = torch.load(_WEIGHTS_FILE, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    return model


def _open_image(image_bytes: bytes) -> Image.Image:
    if not image_bytes:
        raise ValueError("image_bytes is empty")
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except Exception as exc:
        raise ValueError(f"Invalid or unreadable image: {exc}") from exc
    # Re-open after verify() — PIL exhausts the stream during verification.
    img = Image.open(io.BytesIO(image_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")  # type: ignore[assignment]
    return img


def classify(image_bytes: bytes) -> Prediction:
    """Run inference on raw image bytes. Deterministic; p95 < 1.0 s on CPU."""
    model = _load_model()
    img = _open_image(image_bytes)
    tensor = _TRANSFORM(img).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
    probs = torch.softmax(logits, dim=1).squeeze(0)
    top5_vals, top5_indices = torch.topk(probs, k=5)
    top_idx = int(top5_indices[0])
    scores = {name: float(probs[i]) for i, name in enumerate(_CLASS_NAMES)}
    top5 = [
        (_CLASS_NAMES[int(i)], float(v))
        for i, v in zip(top5_indices, top5_vals, strict=False)
    ]
    return Prediction(
        label=_CLASS_NAMES[top_idx],
        top1_confidence=float(probs[top_idx]),
        top5=top5,
        scores=scores,
    )


def make_overlay(image_bytes: bytes, prediction: Prediction) -> bytes:
    """Draw label + confidence on the image. Returns PNG bytes."""
    img = _open_image(image_bytes).convert("RGBA")
    draw = ImageDraw.Draw(img)
    text = f"{prediction.label}  {prediction.top1_confidence:.1%}"
    try:
        font = ImageFont.truetype("arial.ttf", size=24)
    except OSError:
        font = ImageFont.load_default()  # type: ignore[assignment]
    bbox = draw.textbbox((0, 0), text, font=font)
    pad = 6
    rect = (
        bbox[0] - pad,
        bbox[1] - pad,
        bbox[2] + pad,
        bbox[3] + pad,
    )
    draw.rectangle(rect, fill=(0, 0, 0, 160))
    draw.text((bbox[0], bbox[1]), text, font=font, fill=(255, 255, 255, 255))
    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG")
    return out.getvalue()
