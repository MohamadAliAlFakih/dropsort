# Runbook (dropsort)

## Audience

Developers and presenters running the project on a laptop. Infra/UI maintainer: keep commands aligned with the repo as compose and CI land.

## Prerequisites

- Docker and Docker Compose
- `TODO(team):` Python/uv version pins for backend dev if different from README
- Node.js (for **local** frontend dev without Docker)

## Repository layout (high level)

- `app/` — FastAPI backend (`TODO(team):` expand when feature-complete).
- `frontend/` — React + Vite + TypeScript SPA; production via **Dockerfile** + **nginx**.
- `docker-compose.yml` — local stack (`TODO(team):` full service graph when api/workers are wired).
- CI: `.github/workflows/ci.yml`

## Backend (local dev, minimal)

Follow the root **README.md** for the current recommended command sequence. `TODO(team):` replace this section with a single canonical path when `docker compose up` runs the full stack end-to-end.

## Vault seeding (REQUIRED before first `alembic upgrade head`)

Vault dev mode starts empty. The backend lifespan + the Alembic admin seed both fail
without these keys. Run after `docker compose up -d vault` and before any backend boot
or migration:

```bash
# 1) Admin seed used by Alembic revision 0002 to create the initial admin user.
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  dropsort-vault-1 vault kv put secret/admin/initial_password value=<choose-a-password>

# 2) JWT signing key. Generate a fresh 64-char token.
SIGNING_KEY=$(uv run python -c "import secrets; print(secrets.token_urlsafe(64))")
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  dropsort-vault-1 vault kv put secret/jwt signing_key="$SIGNING_KEY"

# 3) Postgres connection URL (async driver for the API; psycopg2 derived in code).
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  dropsort-vault-1 vault kv put secret/postgres \
  url='postgresql+asyncpg://dropsort:dropsort-dev@db:5432/dropsort'

# 4) Redis URL (used by fastapi-cache2 + fastapi-limiter + RQ).
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  dropsort-vault-1 vault kv put secret/redis url='redis://redis:6379/0'

# 5) MinIO credentials.
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  dropsort-vault-1 vault kv put secret/minio \
  root_user=dropsort root_password=dropsort-dev-minio

# 6) SFTP credentials.
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  dropsort-vault-1 vault kv put secret/sftp \
  user=dropsort password=dropsort-dev-sftp

# Verify all keys present:
docker exec -e VAULT_ADDR=http://127.0.0.1:8200 -e VAULT_TOKEN=dropsort-dev-token \
  dropsort-vault-1 vault kv list secret/
# Expected output: admin/, jwt, minio, postgres, redis, sftp
```

**Notes:**
- The container name `dropsort-vault-1` matches `docker compose up`. Adjust if your
  compose project name differs (`docker compose ps` shows actual names).
- These values are intentionally dev defaults that match `docker-compose.yml`'s
  hardcoded `POSTGRES_PASSWORD`/`MINIO_ROOT_PASSWORD`. Production deployments use
  real secrets and rotated tokens.
- If running **outside Docker** (e.g. local `uvicorn`), swap `db`/`redis`/`vault` host
  names to `localhost` and set `VAULT_ADDR=http://localhost:8200` in your shell.

## Demo: refuse-to-start (BOOT-01, BOOT-02, BOOT-03, BOOT-04)

```bash
# Vault unreachable (BOOT-01)
docker compose stop vault
docker compose up api          # exits with VaultUnreachable

# Casbin policy table empty (BOOT-02)
docker exec dropsort-db-1 psql -U dropsort -d dropsort -c "TRUNCATE casbin_rule;"
docker compose up api          # exits with "BOOT-02: casbin_rule table is empty"

# Classifier weights missing (BOOT-03)
rm app/classifier/models/classifier.pt
docker compose up api          # exits with ClassifierBootError

# Model accuracy below threshold (BOOT-04)
MIN_MODEL_TOP1=0.99 docker compose up api    # exits if model test_top1 < 0.99
```

## Frontend — local development (no Docker)

```bash
cd frontend
cp .env.example .env
# Set VITE_API_BASE_URL to your API origin, e.g. http://127.0.0.1:8000
npm install   # or npm ci if package-lock.json is present
npm run dev
```

See `frontend/README.md` for scripts (`build`, `typecheck`, etc.).

## Frontend — Docker Compose (nginx)

The `frontend` service builds the Vite app and serves static files on **container port 80**. The host port is **`FRONTEND_PORT`** (see root `.env.example`).

**Build-time note:** `VITE_API_BASE_URL` must be set in the **root** `.env` (or exported in your shell) before `docker compose build frontend`. It is passed as a Docker build-arg and inlined by Vite. Use an origin your **browser** will use to reach the API (typically `http://127.0.0.1:<API_PORT>` on a laptop), not a Docker-internal hostname, unless every user agent can resolve it.

From the **repository root**:

```bash
cp .env.example .env
# Edit .env if needed: VITE_API_BASE_URL, FRONTEND_PORT
docker compose build frontend
docker compose up -d frontend
```

Open `http://127.0.0.1:${FRONTEND_PORT}` (default **5173** per `.env.example`).

Rebuild after UI changes:

```bash
docker compose build frontend
docker compose up -d frontend
```

## Compose validation (frontend only)

From the repository root, after `.env` exists and includes `VITE_API_BASE_URL`:

```bash
# 1) Image builds (Vite + nginx stage)
docker compose build frontend

# 2) Service starts; host port maps to nginx :80
docker compose up -d frontend

# 3) Service is listed as running
docker compose ps frontend

# 4) nginx serves index (expect HTTP 200)
curl -sS -o /dev/null -w "%{http_code}\n" "http://127.0.0.1:${FRONTEND_PORT:-5173}/"

# 5) Optional: container logs if step 4 is not 200
docker compose logs --tail=50 frontend

# 6) Stop when finished
docker compose stop frontend
```

If step 4 fails, confirm `FRONTEND_PORT` is free on the host and re-check `docker compose logs frontend`.
