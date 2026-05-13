"""CACHE-03 + AUTH-07: role change for X reflects on X's next /me."""

from __future__ import annotations

from httpx import AsyncClient


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


async def test_role_change_reflects_on_next_me(
    client: AsyncClient, admin_token: str, reviewer_token: str
) -> None:
    """Pre: reviewer's /me returns role=reviewer (and caches).
    Admin demotes reviewer to auditor.
    Reviewer's NEXT /me must return role=auditor (cache invalidated, no logout).
    """
    me1 = (await client.get("/me", headers=_auth(reviewer_token))).json()
    assert me1["role"] == "reviewer"

    users = (await client.get("/admin/users", headers=_auth(admin_token))).json()
    reviewer = next(u for u in users if u["email"] == "rev@example.com")

    r = await client.post(
        f"/admin/users/{reviewer['id']}/role",
        headers=_auth(admin_token),
        json={"role": "auditor"},
    )
    assert r.status_code == 200, r.text

    me2 = (await client.get("/me", headers=_auth(reviewer_token))).json()
    assert me2["role"] == "auditor"
