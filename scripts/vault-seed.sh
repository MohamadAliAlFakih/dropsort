#!/usr/bin/env sh
# Idempotent Vault KV seed for local compose and CI.
# Requires: VAULT_ADDR, VAULT_DEV_ROOT_TOKEN (or VAULT_TOKEN) set by the caller / compose.
# Optional: ADMIN_INITIAL_PASSWORD, JWT_SIGNING_KEY (defaults are dev-only).

set -eu

export VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
export VAULT_TOKEN="${VAULT_TOKEN:-${VAULT_DEV_ROOT_TOKEN:-dropsort-dev-token}}"

ADMIN_PW="${ADMIN_INITIAL_PASSWORD:-dropsort-admin-dev}"
JWT_KEY="${JWT_SIGNING_KEY:-local-dev-jwt-signing-key-change-in-prod-48chars-min!!}"

vault kv put secret/admin/initial_password value="${ADMIN_PW}"
vault kv put secret/jwt signing_key="${JWT_KEY}"
vault kv put secret/postgres \
  url='postgresql+asyncpg://dropsort:dropsort-dev@db:5432/dropsort'
vault kv put secret/redis url='redis://redis:6379/0'
vault kv put secret/minio root_user=dropsort root_password=dropsort-dev-minio
vault kv put secret/sftp user=dropsort password=dropsort-dev-sftp

echo "vault-seed: KV paths under secret/ are ready."
