"""Grep gates encoded as tests (API-02, API-03, CACHE-04, DB-04, VAULT-04)."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _grep(pattern: str, path: str) -> tuple[int, str]:
    r = subprocess.run(
        ["git", "grep", "-nE", pattern, "--", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode, r.stdout


def test_api_02_no_sqlalchemy_in_routers() -> None:
    """API-02: app/api/*.py doesn't import sqlalchemy at top level (deps.py + inline in
    health.py are allowed)."""
    rc, out = _grep("^from sqlalchemy|^import sqlalchemy", "app/api/")
    if rc == 1:
        return  # no matches
    # Only allow inline (non-top-level) imports - all top-level matches are violations.
    bad = [
        line
        for line in out.splitlines()
        if line.strip() and "app/api/deps.py" not in line
    ]
    assert not bad, "API-02 violation:\n" + "\n".join(bad)


def test_cache_04_invalidation_only_in_services() -> None:
    """CACHE-04: FastAPICache.clear lives only in app/services/."""
    rc, out = _grep(r"FastAPICache\.clear", "app/")
    if rc == 1:
        return
    bad = [line for line in out.splitlines() if not line.startswith("app/services/")]
    assert not bad, "CACHE-04 violation:\n" + "\n".join(bad)


def test_api_03_no_httpexception_in_repositories() -> None:
    """API-03: repositories never raise HTTPException."""
    rc, out = _grep("HTTPException", "app/repositories/")
    if rc == 1:
        return
    # Allow docstrings/comments mentioning the rule.
    bad = [line for line in out.splitlines() if 'HTTPException"' not in line and "# " not in line]
    bad = [line for line in bad if "raise HTTPException" in line or "from fastapi" in line]
    assert not bad, "API-03 violation:\n" + "\n".join(bad)


def test_db_04_orm_only_in_allowed_paths() -> None:
    """DB-04: `from app.db.models` allowed only in repositories + auth_service + deps."""
    rc, out = _grep(r"from app\.db\.models", "app/")
    if rc == 1:
        return
    allowed_prefixes = (
        "app/repositories/",
        "app/services/auth_service.py",
        "app/api/deps.py",
        "app/infra/casbin/enforcer.py",  # imports CasbinRule for policy count
    )
    bad = [line for line in out.splitlines() if not line.startswith(allowed_prefixes)]
    assert not bad, "DB-04 violation:\n" + "\n".join(bad)


def test_vault_04_password_outside_vault_only_in_known_locations() -> None:
    """VAULT-04: literal 'password' in app/ only in vault.py + user_service.py (invite arg)."""
    rc, out = _grep("password", "app/")
    if rc == 1:
        return
    allowed_prefixes = (
        "app/core/vault.py",
        "app/services/user_service.py",  # invite has `password: str` parameter
        "app/services/auth_service.py",  # fastapi-users password helper mention
        "app/db/models.py",  # SQLAlchemyBaseUserTableUUID contains hashed_password
    )
    bad = [line for line in out.splitlines() if not line.startswith(allowed_prefixes)]
    assert not bad, "VAULT-04 violation:\n" + "\n".join(bad)
