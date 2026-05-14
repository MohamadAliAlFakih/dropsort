#!/usr/bin/env sh
# Idempotent dev-Vault seeder. Run after `docker compose up -d vault`.
# Re-running is safe: existing paths are skipped (Vault dev mode wipes on restart,
# so a fresh container always needs full seeding).
#
# Usage:
#   ./scripts/seed-vault.sh                  # uses defaults
#   ADMIN_PASSWORD=mypass ./scripts/seed-vault.sh

set -eu

VAULT_CONTAINER="${VAULT_CONTAINER:-dropsort-vault-1}"
VAULT_ADDR_INTERNAL="${VAULT_ADDR_INTERNAL:-http://127.0.0.1:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-dropsort-dev-token}"

ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin-dev-pass}"
JWT_SIGNING_KEY="${JWT_SIGNING_KEY:-$(python -c 'import secrets; print(secrets.token_urlsafe(64))' 2>/dev/null || echo "dev-jwt-key-replace-me-with-something-longer-than-32-chars")}"

vex() {
  docker exec -e VAULT_ADDR="$VAULT_ADDR_INTERNAL" -e VAULT_TOKEN="$VAULT_TOKEN" "$VAULT_CONTAINER" "$@"
}

has_secret() {
  vex vault kv get "secret/$1" >/dev/null 2>&1
}

put_if_missing() {
  path="$1"; shift
  if has_secret "$path"; then
    echo "  [skip] secret/$path already exists"
  else
    echo "  [seed] secret/$path"
    vex vault kv put "secret/$path" "$@" >/dev/null
  fi
}

echo "Seeding Vault at $VAULT_CONTAINER..."

put_if_missing "admin/initial_password" "value=$ADMIN_PASSWORD"
put_if_missing "jwt"                    "signing_key=$JWT_SIGNING_KEY"
put_if_missing "postgres"               "url=postgresql+asyncpg://dropsort:dropsort-dev@db:5432/dropsort"
put_if_missing "redis"                  "url=redis://redis:6379/0"
put_if_missing "minio"                  "root_user=dropsort" "root_password=dropsort-dev-minio"
put_if_missing "sftp"                   "user=dropsort"      "password=dropsort-dev-sftp"

echo "Done."
