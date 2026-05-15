"""POST /batches/upload — Casbin and happy-path smoke (stack required)."""

from __future__ import annotations

from io import BytesIO

from httpx import AsyncClient
from PIL import Image


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


async def test_auditor_cannot_upload_tiff(client: AsyncClient, auditor_token: str) -> None:
    r = await client.post(
        "/batches/upload",
        headers=_auth(auditor_token),
        files={"file": ("doc.tif", b"not-a-real-tiff", "image/tiff")},
    )
    assert r.status_code == 403, r.text


async def test_reviewer_upload_tiff_enqueues(
    client: AsyncClient, reviewer_token: str
) -> None:
    buf = BytesIO()
    Image.new("RGB", (8, 8), color=(200, 200, 200)).save(buf, format="TIFF")
    body = buf.getvalue()

    r = await client.post(
        "/batches/upload",
        headers=_auth(reviewer_token),
        files={"file": ("page.tif", body, "image/tiff")},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert "batch" in data and "job_id" in data
    assert data["batch"]["state"] == "received"
