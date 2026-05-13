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
