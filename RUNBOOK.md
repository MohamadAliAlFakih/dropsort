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
- `TODO(team):` `.github/workflows` once CI is merged.

## Backend (local dev, minimal)

Follow the root **README.md** for the current recommended command sequence. `TODO(team):` replace this section with a single canonical path when `docker compose up` runs the full stack end-to-end.

## Frontend — local development (no Docker)

```bash
cd frontend
cp .env.example .env
# Set VITE_API_BASE_URL to your API origin, e.g. http://localhost:8000
npm install   # or npm ci if package-lock.json is present
npm run dev