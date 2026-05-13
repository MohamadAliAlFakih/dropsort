"""Vault adapter - the ONE place in app/ that accesses Vault.

Per VAULT-04 grep gate: this module is the canonical home for `password`-bearing reads.
Routers, services, repositories NEVER touch Vault directly - they read `app.state.secrets`.

Per Engineering Standards ch.3: secrets resolved during lifespan, stored on app.state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import hvac
import structlog

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ResolvedSecrets:
    """All secrets needed by api + workers, resolved once at boot."""

    jwt_signing_key: str
    postgres_url: str
    redis_url: str
    minio_root_user: str
    minio_root_password: str
    sftp_user: str
    sftp_password: str


class VaultUnreachable(RuntimeError):
    """BOOT-01: api refuses to start when this is raised."""


def resolve_secrets() -> ResolvedSecrets:
    """Single source of truth for all secret reads. Called once in lifespan."""
    settings = get_settings()
    client = hvac.Client(url=settings.vault_addr, token=settings.vault_dev_root_token)

    if not client.is_authenticated():
        raise VaultUnreachable(
            f"Vault at {settings.vault_addr} did not authenticate the dev root token. "
            "BOOT-01: api refuses to start."
        )

    start = time.monotonic()
    try:
        jwt = _read_kv(client, "jwt")["signing_key"]
        pg = _read_kv(client, "postgres")
        redis = _read_kv(client, "redis")
        minio = _read_kv(client, "minio")
        sftp = _read_kv(client, "sftp")
    except hvac.exceptions.VaultError as exc:
        raise VaultUnreachable(f"Vault read failed: {exc}") from exc
    elapsed_ms = int((time.monotonic() - start) * 1000)

    logger.info(
        "secrets_resolved",
        elapsed_ms=elapsed_ms,
        keys=["jwt", "postgres", "redis", "minio", "sftp"],
    )

    return ResolvedSecrets(
        jwt_signing_key=jwt,
        postgres_url=pg["url"],
        redis_url=redis["url"],
        minio_root_user=minio["root_user"],
        minio_root_password=minio["root_password"],
        sftp_user=sftp["user"],
        sftp_password=sftp["password"],
    )


def health_check() -> tuple[bool, int, str | None]:
    """For /health. Returns (ok, latency_ms, error?)."""
    settings = get_settings()
    client = hvac.Client(url=settings.vault_addr, token=settings.vault_dev_root_token)
    start = time.monotonic()
    try:
        ok = client.sys.is_initialized() and not client.sys.is_sealed()
        return (bool(ok), int((time.monotonic() - start) * 1000), None)
    except Exception as exc:  # noqa: BLE001
        return (False, int((time.monotonic() - start) * 1000), str(exc)[:200])


def _read_kv(client: hvac.Client, path: str) -> dict[str, str]:
    response = client.secrets.kv.v2.read_secret_version(path=path)
    return response["data"]["data"]
