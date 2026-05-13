"""Pydantic Settings - single source of truth for all env-derived configuration.

Per API-06 and CONTEXT D-11:
- extra='forbid' makes typos in .env fail loudly at startup.
- `os.getenv` is allowed ONLY in this module.
- All secrets (Vault token, DB URL, JWT signing key, MinIO creds, SFTP creds, etc.)
  resolve from Vault at startup (Phase 3 wires app/core/vault.py). This Settings class
  carries only the values needed to *reach* Vault and bind to the right ports.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings - bootstrap surface only.

    Phase 1 carries: Vault dev token + service ports + log level + MIN_MODEL_TOP1 placeholder.
    Phase 3 extends with DB URL, Redis URL, MinIO endpoint (each resolved from Vault during
    lifespan, NOT from env). Phase 2 wires the classifier-related env vars.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        case_sensitive=False,
    )

    # --- Vault (dev mode) ---
    vault_dev_root_token: str = Field(
        default="dropsort-dev-token",
        description="Vault dev-mode root token. Phase 3 uses this to bootstrap real secret reads.",
    )
    vault_addr: str = Field(default="http://vault:8200")

    # --- Service ports ---
    api_port: int = 8000
    frontend_port: int = 5173
    postgres_port: int = 5432
    redis_port: int = 6379
    minio_api_port: int = 9000
    minio_console_port: int = 9001
    sftp_port: int = 2222
    vault_port: int = 8200

    # --- Pipeline / local compose defaults ---
    redis_url: str = "redis://redis:6379/0"
    rq_queue_name: str = "classification"

    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "dropsort"
    minio_secret_key: str = "dropsort-dev-minio"  # noqa: S105 -- dev fallback; prod via Vault
    minio_bucket: str = "documents"
    minio_secure: bool = False

    sftp_host: str = "sftp"
    sftp_port_internal: int = 22
    sftp_username: str = "dropsort"
    sftp_secret: str = "dropsort-dev-sftp"  # noqa: S105 -- dev fallback; prod via Vault
    sftp_watch_dir: str = "/incoming"
    sftp_poll_interval_seconds: int = 5

    pipeline_max_file_size_mb: int = 25
    
    # --- Observability ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Classifier refuse-to-start threshold (BOOT-04) ---
    min_model_top1: float | None = Field(
        default=None,
        description=(
            "Refuse-to-start threshold. Phase 2 (Saleh) sets this post-Colab-eval. "
            "Phase 1 only wires the env var; api/worker boot only checks this in Phase 3+ once "
            "model_card.json exists."
        ),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Memoised Settings accessor. Use as a FastAPI dependency."""
    return Settings()
