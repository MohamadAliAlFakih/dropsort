"""Admin user lifecycle: PATCH active, soft DELETE, guards, audit."""

from __future__ import annotations

import uuid

import pytest_asyncio
from httpx import AsyncClient


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


@pytest_asyncio.fixture
async def fresh_reviewer(client: AsyncClient, admin_token: str) -> dict[str, str]:
    """New reviewer each test (avoids 409 / stale state from prior runs)."""
    email = f"lifecycle-{uuid.uuid4().hex[:12]}@example.com"
    r = await client.post(
        "/admin/users/invite",
        headers=_auth(admin_token),
        json={
            "email": email,
            "initial_secret": "TempPw1234!",
            "role": "reviewer",
        },
    )
    assert r.status_code == 201, r.text
    return {"id": r.json()["id"], "email": email}


async def test_admin_deactivate_reactivate_reviewer(
    client: AsyncClient, admin_token: str, fresh_reviewer: dict[str, str]
) -> None:
    auth = _auth(admin_token)
    rid = fresh_reviewer["id"]

    r = await client.patch(
        f"/admin/users/{rid}/active",
        headers=auth,
        json={"is_active": False},
    )
    assert r.status_code == 200, r.text
    assert r.json()["is_active"] is False

    users = (await client.get("/admin/users", headers=auth)).json()
    row = next(u for u in users if u["id"] == rid)
    assert row["is_active"] is False
    assert row.get("deleted_at") in (None, "")

    r2 = await client.patch(
        f"/admin/users/{rid}/active",
        headers=auth,
        json={"is_active": True},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["is_active"] is True


async def test_admin_cannot_patch_own_active(
    client: AsyncClient, admin_token: str
) -> None:
    me = (await client.get("/me", headers=_auth(admin_token))).json()
    r = await client.patch(
        f"/admin/users/{me['id']}/active",
        headers=_auth(admin_token),
        json={"is_active": False},
    )
    assert r.status_code == 400, r.text


async def test_admin_cannot_lifecycle_other_admin(
    client: AsyncClient, admin_token: str
) -> None:
    auth = _auth(admin_token)
    email = f"admin-peer-{uuid.uuid4().hex[:12]}@example.com"
    inv = await client.post(
        "/admin/users/invite",
        headers=auth,
        json={
            "email": email,
            "initial_secret": "AdminPeerPw1!",
            "role": "admin",
        },
    )
    assert inv.status_code == 201, inv.text
    peer_id = inv.json()["id"]

    r = await client.patch(
        f"/admin/users/{peer_id}/active",
        headers=auth,
        json={"is_active": False},
    )
    assert r.status_code == 403, r.text

    d = await client.delete(f"/admin/users/{peer_id}", headers=auth)
    assert d.status_code == 403, d.text


async def test_soft_delete_reviewer_then_404_on_repeat(
    client: AsyncClient, admin_token: str, fresh_reviewer: dict[str, str]
) -> None:
    auth = _auth(admin_token)
    rid = fresh_reviewer["id"]
    prior_email = fresh_reviewer["email"]

    r = await client.delete(f"/admin/users/{rid}", headers=auth)
    assert r.status_code == 204, r.text

    users = (await client.get("/admin/users", headers=auth)).json()
    row = next(u for u in users if u["id"] == rid)
    assert row["deleted_at"] is not None
    assert row["is_active"] is False
    assert row.get("original_email") == prior_email
    assert row["email"].startswith("removed.")
    assert prior_email not in row["email"]

    r2 = await client.delete(f"/admin/users/{rid}", headers=auth)
    assert r2.status_code == 404, r2.text

    r3 = await client.patch(
        f"/admin/users/{rid}/active",
        headers=auth,
        json={"is_active": True},
    )
    assert r3.status_code == 404, r3.text


async def test_lifecycle_audit_entries(
    client: AsyncClient, admin_token: str, fresh_reviewer: dict[str, str]
) -> None:
    auth = _auth(admin_token)
    rid = fresh_reviewer["id"]

    await client.patch(
        f"/admin/users/{rid}/active",
        headers=auth,
        json={"is_active": False},
    )
    await client.patch(
        f"/admin/users/{rid}/active",
        headers=auth,
        json={"is_active": True},
    )
    await client.delete(f"/admin/users/{rid}", headers=auth)

    audit = (await client.get("/audit", headers=auth)).json()
    actions = [e["action"] for e in audit if e.get("target_id") == rid]
    assert "user_deactivated" in actions
    assert "user_reactivated" in actions
    assert "user_deleted" in actions
