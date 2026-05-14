"""Audit row written after every state-changing action (API-07)."""

from __future__ import annotations

from httpx import AsyncClient


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


async def test_role_change_writes_audit_row(
    client: AsyncClient, admin_token: str, reviewer_token: str
) -> None:
    """Change a role -> audit row 'role_changed' exists."""
    audit_before = (await client.get("/audit", headers=_auth(admin_token))).json()
    count_before = len(audit_before)

    users = (await client.get("/admin/users", headers=_auth(admin_token))).json()
    reviewer = next((u for u in users if u["email"] == "rev@example.com"), None)
    assert reviewer is not None

    r = await client.post(
        f"/admin/users/{reviewer['id']}/role",
        headers=_auth(admin_token),
        json={"role": "auditor"},
    )
    assert r.status_code == 200, r.text

    audit_after = (await client.get("/audit", headers=_auth(admin_token))).json()
    assert len(audit_after) > count_before
    actions = [e["action"] for e in audit_after]
    assert "role_changed" in actions
    entry = next(e for e in audit_after if e["action"] == "role_changed")
    assert "actor_email" in entry and entry.get("actor_email")
    assert "target_label" in entry and entry.get("target_label")
