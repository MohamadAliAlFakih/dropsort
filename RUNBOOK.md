# Runbook (dropsort)

Audience: developers and presenters running the stack on a laptop, plus CI operators.

## Prerequisites

- **Docker** + **Docker Compose v2**
- **Git LFS** (`git lfs install`) — `classifier.pt` is an LFS object
- **Node 20+** only if you develop the SPA with Vite outside Docker

## Fresh clone → full stack (recommended)

From the repository root:

```bash
git lfs pull
cp .env.example .env
# Optional: edit .env — ports, ADMIN_INITIAL_PASSWORD, JWT_SIGNING_KEY, VITE_API_BASE_URL
docker compose build api frontend
docker compose up -d
```

**What starts, in order:**

1. **Postgres, Redis, Vault, MinIO, SFTP** — wait until healthy.
2. **`vault-seed`** — writes KV paths under `secret/` (see ARCH.md).
3. **`migrate`** — `alembic upgrade head` (schema + Casbin + admin user).
4. **`api`**, **`worker`**, **`sftp-ingest`** — depend on migrate completing.
5. **`frontend`** — starts only after **`api`** healthcheck returns HTTP 200 with **`"ok": true`**.

**URLs (defaults from `.env.example`):**

| Service | URL |
|---------|-----|
| API | `http://127.0.0.1:8000` (or `http://127.0.0.1:${API_PORT}`) |
| API health | `GET http://127.0.0.1:8000/health` |
| SPA (nginx) | `http://127.0.0.1:${FRONTEND_PORT}` — container listens on **80**, host maps to **5173** by default |

**First login:** `admin@example.com` with password from **`ADMIN_INITIAL_PASSWORD`** in `.env` (default **`dropsort-admin-dev`**, matching `scripts/vault-seed.sh`).

## CI smoke (same flow as GitHub Actions)

Requires Docker. From repo root:

```bash
export ADMIN_INITIAL_PASSWORD=ci-smoke-admin-pw   # optional override
export JWT_SIGNING_KEY='ci-smoke-jwt-signing-key-thirty-two-chars-minimum!!'
bash scripts/ci_smoke.sh
```

The script: builds **`api`**, brings up **`db` `redis` `vault` `minio` `sftp` `vault-seed` `migrate` `api` `worker`**, waits for **`/health`**, logs in, **`POST /batches/upload`** with a golden TIFF, polls **`GET /predictions/recent`** until at least one row exists (timeouts configurable via `SMOKE_*` env vars in the script).

## Manual Vault KV (debug only)

Normally **`vault-seed`** handles this. To re-run against a running Vault container:

```bash
docker compose up -d vault
# wait until healthy, then:
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  <vault-container-name> vault kv put secret/admin/initial_password value='<password>'
# …repeat jwt, postgres, redis, minio, sftp per ARCH.md, or run scripts/vault-seed.sh inside a vault image on the compose network.
```

## Refuse-to-start demos (API)

With the stack configured, see **SECURITY.md** / course brief for threat framing. Quick API checks from the repo root:

```bash
# Vault stopped → API lifespan raises VaultUnreachable
docker compose stop vault
docker compose up api   # expect failure
docker compose start vault

# Empty Casbin → BOOT-02
docker exec <postgres-container> psql -U dropsort -d dropsort -c "TRUNCATE casbin_rule;"
docker compose up api   # expect failure; then re-run migrate from a good DB backup or volume reset

# Missing weights → BOOT-03 (restore from git lfs after)
# MIN_MODEL_TOP1 above card metric → BOOT-04 when env set
```

## Frontend — local Vite (no Docker)

```bash
cd frontend
cp .env.example .env
# Set VITE_API_BASE_URL to your API, e.g. http://127.0.0.1:8000
npm install
npm run dev
```

## Frontend — Docker rebuild after UI changes

`VITE_API_BASE_URL` is baked at **build** time:

```bash
docker compose build frontend
docker compose up -d frontend
```

## Compose validation (frontend only)

```bash
docker compose build frontend
docker compose up -d frontend
curl -sS -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:${FRONTEND_PORT:-5173}/"
```

## Backend tests (integration, host Python)

Integration tests in `tests/` expect **Postgres, Redis, and Vault** on localhost ports and a migrated DB (see `tests/conftest.py`). Typical host workflow:

```bash
docker compose up -d db redis vault
export ADMIN_INITIAL_PASSWORD=test-admin-pw   # must match what Alembic used / Vault seed
export VAULT_ADDR=http://127.0.0.1:8200
# Seed Vault if empty (see scripts/vault-seed.sh logic), then:
uv run alembic upgrade head
uv run pytest
```

## Related

- **[README.md](./README.md)** — project overview and layout
- **[ARCH.md](./ARCH.md)** — topology and CI list
