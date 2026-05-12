# dropsort

AIE39 Week 6 group project — RVL-CDIP document classifier behind a layered, permission-gated FastAPI service with SFTP ingestion, RQ-based inference pipeline, and a React+Vite frontend.

## Team

Fakih (MA), Nasser, Saleh, Shari.

## First-time setup

```bash
cp .env.example .env
uv sync
docker compose up db redis vault minio sftp
uv run uvicorn app.main:app --reload
```

Then visit http://localhost:8000/health.

## Required docs (Phase 5)

- [ARCH.md](./ARCH.md) — architecture diagram and layer walk-through
- [DECISIONS.md](./DECISIONS.md) — key design decisions with rationale
- [RUNBOOK.md](./RUNBOOK.md) — first-time setup, demo steps, latency commands
- [SECURITY.md](./SECURITY.md) — threat model, secrets posture, grep gate
- [COLLABORATION.md](./COLLABORATION.md) — Trello link and team notes
- [LICENSES.md](./LICENSES.md) — RVL-CDIP academic-use note and project license

## Refuse-to-start

`api` and `worker` refuse to boot if:
- Vault is unreachable
- Casbin policy table is empty
- `app/classifier/models/classifier.pt` is missing or SHA-256 does not match `model_card.json`
- model card `test_top1` is below `MIN_MODEL_TOP1` (env var, set per RUNBOOK)

## Layout

- `app/` — Python backend (layered: api -> services -> repositories -> db/models)
- `frontend/` — React + Vite + TypeScript (Phase 5b)
- `notebook/` — Colab training notebook (Phase 2, committed)
- `alembic/` — database migrations
- `scripts/` — Vault seed + other operational scripts
- `docker-compose.yml` — full local stack

## Status

Phase 1 (bootstrap) — repo skeleton, layered `app/`, baseline tooling, structured logging, request-id middleware, empty Alembic, compose skeleton.
