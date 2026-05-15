"""Casbin policy matrix - AUTH-05."""

from __future__ import annotations

from httpx import AsyncClient


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


async def test_admin_can_read_audit(client: AsyncClient, admin_token: str) -> None:
    r = await client.get("/audit", headers=_auth(admin_token))
    assert r.status_code == 200, r.text


async def test_reviewer_cannot_read_audit(
    client: AsyncClient, reviewer_token: str
) -> None:
    """AUTH-03: authenticated but unauthorized -> 403."""
    r = await client.get("/audit", headers=_auth(reviewer_token))
    assert r.status_code == 403


async def test_auditor_can_read_audit(
    client: AsyncClient, auditor_token: str
) -> None:
    r = await client.get("/audit", headers=_auth(auditor_token))
    assert r.status_code == 200, r.text


async def test_auditor_cannot_invite_users(
    client: AsyncClient, auditor_token: str
) -> None:
    r = await client.post(
        "/admin/users/invite",
        headers=_auth(auditor_token),
        json={"email": "x@example.com", "password": "pw1234", "role": "reviewer"},
    )
    assert r.status_code == 403


async def test_admin_cannot_relabel(client: AsyncClient, admin_token: str) -> None:
    """Per CONTEXT specifics: admin has no PATCH policy on /predictions/*."""
    r = await client.patch(
        "/predictions/00000000-0000-0000-0000-000000000000",
        headers=_auth(admin_token),
        json={"label": "letter"},
    )
    assert r.status_code == 403


async def test_reviewer_can_list_batches(
    client: AsyncClient, reviewer_token: str
) -> None:
    r = await client.get("/batches", headers=_auth(reviewer_token))
    assert r.status_code == 200, r.text
