# dropsort

AIE39 Week 6 group project — **RVL-CDIP**–style document classification behind a **layered FastAPI** API, **Casbin** RBAC, **Vault**-backed secrets, **RQ** workers, and a **React + Vite** SPA.

**Team:** Fakih (MA), Nasser, Saleh, Shari.

## Quick start (Docker, full stack)

```bash
git clone <repo-url>
cd dropsort
git lfs pull
cp .env.example .env
docker compose build api frontend
docker compose up -d
```

- **API:** `http://127.0.0.1:${API_PORT:-8000}` — `GET /health` for readiness (`ok: true` when Postgres, Redis, Vault, and Casbin checks pass).
- **UI:** `http://127.0.0.1:${FRONTEND_PORT:-5173}` — nginx serves the built SPA; **`VITE_API_BASE_URL`** must match how your browser reaches the API (see `.env.example`).

Default admin login: **`admin@example.com`** / password from **`ADMIN_INITIAL_PASSWORD`** (default **`dropsort-admin-dev`**, written to Vault by the **`vault-seed`** service).

## Layout

| Path | Purpose |
|------|---------|
| `app/` | FastAPI backend: `api/` → `services/` → `repositories/` → `db/models` |
| `app/classifier/` | ConvNeXt inference, `model_card.json`, boot checks, `eval/golden.py` |
| `app/workers/` | RQ inference worker, SFTP ingest, job handlers |
| `frontend/` | React + Vite + TypeScript SPA |
| `alembic/` | Database migrations (schema + Casbin seed + admin) |
| `scripts/` | `vault-seed.sh`, `ci_smoke.sh` |
| `docker-compose.yml` | Local stack and boot ordering |
| `.github/workflows/ci.yml` | Lint, typecheck, tests, **golden replay**, **Docker API build**, **compose smoke** |

## Required documentation

- [ARCH.md](./ARCH.md) — topology, layering, Vault paths, CI overview  
- [DECISIONS.md](./DECISIONS.md) — ADRs  
- [RUNBOOK.md](./RUNBOOK.md) — fresh clone, ports, smoke script, refuse-to-start demos  
- [SECURITY.md](./SECURITY.md) — secrets, RBAC, classifier integrity  
- [COLLABORATION.md](./COLLABORATION.md) — team process (Trello link is maintained by the group)  
- [LICENSES.md](./LICENSES.md) — RVL-CDIP and third-party notices  

## Refuse-to-start (high level)

The **API** and **inference worker** exit on startup if: Vault is unreachable; Casbin policy table is empty; **`classifier.pt`** is missing or its SHA does not match **`model_card.json`**; or (when set) **`MIN_MODEL_TOP1`** exceeds the model card **`test_top1`**. Details: [RUNBOOK.md](./RUNBOOK.md), [SECURITY.md](./SECURITY.md).

## Local API without full stack

For lightweight development you can run only infra + uvicorn (you still need Vault seeded and migrations applied — see [RUNBOOK.md](./RUNBOOK.md)):

```bash
docker compose up -d db redis vault minio sftp
# ensure Vault KV + alembic upgrade (see RUNBOOK)
uv sync
uv run uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```
