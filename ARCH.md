# Architecture (dropsort)

## Scope of this document

This file describes the **intended** Week 6 architecture and what is **already in the repository**. Anything not yet merged is marked `TODO(team)`.

## Product overview

dropsort is a local, docker-compose–oriented document classification service: documents arrive via SFTP, a pipeline classifies them, and authenticated users review results through an API and UI. `TODO(team):` one-sentence refinement once the API surface is frozen.

## Runtime topology (target)

The laptop stack is intended to include:

- **API** — FastAPI application (`TODO(team):` routers, auth, caching).
- **Workers** — ingestion from SFTP and inference / queue consumers (`TODO(team):` entrypoints and boundaries per layered design).
- **Data plane** — PostgreSQL, Redis, MinIO, SFTP, Vault (`TODO(team):` exact wiring and health/startup order in compose).
- **Frontend** — static SPA served separately from the API.

`TODO(team):` insert a diagram (Mermaid or exported image) when stable.

## Layered backend (brief)

The Python codebase follows a fixed layering model (API → services → repositories → ORM; domain models; infra adapters). `TODO(team):` link to module-level examples once Phase 3/4 land.

## Frontend (implemented baseline)

The **frontend** lives under `frontend/` and is built with:

- **React**, **Vite**, and **TypeScript**
- Production image: **multi-stage Docker** build (Node build → **nginx** serving static files on port 80)
- API base URL: **`VITE_API_BASE_URL`** (inlined at Vite build time; supplied via Docker build args / CI, not hardcoded in application source)

Routing and a minimal API client live in `frontend/src/`; the only guaranteed backend call in the scaffold is **`GET /health`**. `TODO(team):` extend client and pages when JWT and domain endpoints exist.

## Secrets and configuration

Secrets are intended to resolve from **Vault** at API/worker startup per project brief. `TODO(team):` document KV paths, seed scripts, and compose bootstrap. The frontend bundle must **not** embed server secrets; only public build-time settings such as `VITE_API_BASE_URL`.

## CI and quality gates

`TODO(team):` document GitHub Actions jobs (lint, typecheck, image build, golden-set test, compose smoke) once merged.

## Related documents

- [DECISIONS.md](./DECISIONS.md) — recorded trade-offs.
- [RUNBOOK.md](./RUNBOOK.md) — how to run locally and demo.
- [SECURITY.md](./SECURITY.md) — secrets and review posture.