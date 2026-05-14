# Architecture decisions (dropsort)

Short entries: **context**, **decision**, **consequences**.

---

### ADR-001 — Frontend stack

- **Context:** Need a small SPA for the Week 6 UI track.
- **Decision:** **React + Vite + TypeScript**; auth state in **React Context**; **React Router** for navigation.
- **Consequences:** Low ceremony; JWT bearer stored client-side for API calls.

---

### ADR-002 — Frontend production delivery

- **Context:** API and UI are separate processes; production images should stay small and cache-friendly.
- **Decision:** **Multi-stage Docker** for `frontend/`: Node builds static assets; **nginx** serves `dist/` on container port **80**; host maps **`FRONTEND_PORT`** (default **5173**).
- **Consequences:** `VITE_API_BASE_URL` is fixed at **image build** time (Vite). Changing the API origin requires rebuilding the frontend image (or a future runtime-config pattern).

---

### ADR-003 — API base URL from environment

- **Context:** Avoid hardcoding API origins per environment.
- **Decision:** **`VITE_API_BASE_URL`** for browser calls; validated in the frontend API client.
- **Consequences:** Compose and CI must pass the build-arg; during local dev the browser must reach the host-mapped API port. Server-side CORS middleware is not used today because the SPA is typically served from a different origin on localhost; if you front both behind one origin, CORS stays unnecessary.

---

### ADR-004 — Vault seeding and Compose boot order

- **Context:** Alembic `0002` reads the admin password from Vault; the API refuses to start without KV secrets and non-empty Casbin rules. Developers expect `docker compose up` to work on a fresh laptop without a long manual Vault dance.
- **Decision:** A one-shot **`vault-seed`** service runs **`scripts/vault-seed.sh`** after Vault is healthy; **`migrate`** depends on successful completion of **`vault-seed`**; **`api`**, **`worker`**, and **`sftp-ingest`** depend on successful completion of **`migrate`**. Optional overrides: **`ADMIN_INITIAL_PASSWORD`** and **`JWT_SIGNING_KEY`** in `.env` are passed into the seed container.
- **Consequences:** First boot is deterministic; re-runs are idempotent (`vault kv put` overwrites). CI smoke uses the same script with CI-specific passwords via environment.

---

### ADR-005 — Classifier quality gates

- **Context:** Course brief requires regression protection on shipped weights.
- **Decision:** **`app/classifier/boot_checks.py`** enforces presence of `classifier.pt` + `model_card.json`, **SHA-256** match, and **`MIN_MODEL_TOP1`** vs `metrics.test_top1` **only when the env var is set** (strict mode for demos/CI); **`app/classifier/eval/golden.py`** replays 50 golden TIFFs with **byte-identical labels** and **top-1 within 1e-6**, run in CI via **`uv run pytest app/classifier/eval/golden.py`**.
- **Consequences:** CI needs **Git LFS** for weights; CPU inference in smoke/golden can take minutes on GitHub runners—timeouts in `scripts/ci_smoke.sh` are set accordingly.

---

### ADR-006 — Cache invalidation ownership

- **Context:** Stale list/detail pages after writes.
- **Decision:** **`FastAPICache.clear(...)`** runs only in **services** after successful commits; routers may apply **`@cache`** decorators but never call clear.
- **Consequences:** Workers that call `record_prediction` / `mark_batch_failed` initialize a short-lived Redis-backed cache backend (`app/workers/cache_context.py`) so invalidation from worker processes works.
