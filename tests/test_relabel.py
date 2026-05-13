"""Relabel guard: top1 < 0.7 allowed; >= 0.7 returns 409 (AUTH-05).

Seeding uses a synchronous psycopg2 engine (separate process resource) so we don't
collide with the test's async DB engine.
"""

from __future__ import annotations

import uuid

from httpx import AsyncClient
from sqlalchemy import create_engine, text


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


SYNC_DB_URL = "postgresql+psycopg2://dropsort:dropsort-dev@localhost:5432/dropsort"


def _seed_prediction(top1: float) -> uuid.UUID:
    """Seed a batch + prediction synchronously. Returns the prediction id."""
    engine = create_engine(SYNC_DB_URL)
    try:
        with engine.begin() as conn:
            bid = uuid.uuid4()
            conn.execute(
                text(
                    "INSERT INTO batches (id, external_id, state) "
                    "VALUES (:id, :ext, 'received')"
                ),
                {"id": bid, "ext": f"test-{bid}"},
            )
            pid = uuid.uuid4()
            conn.execute(
                text(
                    "INSERT INTO predictions "
                    "(id, batch_id, filename, content_sha256, minio_input_key, "
                    " label, top1_confidence, top5_json) "
                    "VALUES (:id, :bid, :fn, :sha, :key, :label, :top1, "
                    "        CAST(:top5 AS jsonb))"
                ),
                {
                    "id": pid,
                    "bid": bid,
                    "fn": f"{bid}.tif",
                    "sha": uuid.uuid4().hex,
                    "key": "k",
                    "label": "letter",
                    "top1": top1,
                    "top5": '[{"label":"letter","score":' + str(top1) + "}]",
                },
            )
        return pid
    finally:
        engine.dispose()


async def test_relabel_low_conf_succeeds(
    client: AsyncClient, reviewer_token: str
) -> None:
    pid = _seed_prediction(0.4)
    r = await client.patch(
        f"/predictions/{pid}",
        headers=_auth(reviewer_token),
        json={"label": "form"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["relabel_label"] == "form"


async def test_relabel_high_conf_returns_409(
    client: AsyncClient, reviewer_token: str
) -> None:
    pid = _seed_prediction(0.95)
    r = await client.patch(
        f"/predictions/{pid}",
        headers=_auth(reviewer_token),
        json={"label": "form"},
    )
    assert r.status_code == 409, r.text
