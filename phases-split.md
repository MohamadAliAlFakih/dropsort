# dropsort — Phases Split

One section per role.

| Track | Owner |
|---|---|
| CLF — Classifier | **Saleh** |
| API — Service + Cross-track coordination | **Fakih** |
| PIPE — Workers | **Nasser** |
| INFRA — Infrastructure + UI (React+Vite) | **Shari** |

> **About "Use cases":** A use case is one user goal and the system's full response to it — not an endpoint, not a function. Read your use cases as the **contract you're shipping**. If your code returns the right HTTP code but skips an audit row a use case requires, the use case is broken even though the endpoint "works". Use them to plan, to test against, and to demo on Friday.

---

## CLF — Classifier Owner (Saleh)

### Tasks (brief)

- Fine-tune `torchvision` ConvNeXt Tiny on RVL-CDIP **on Colab** (37 GB dataset, never local).
- Evaluate on the full 40k test split.
- Pick 50 golden TIFFs spanning all 16 classes, mix easy + ambiguous.
- Build `classify()` and `make_overlay()` for other tracks to consume.

### Deliverables (brief)

- `app/classifier/models/classifier.pt` (~110 MB, **Git LFS**).
- `app/classifier/models/model_card.json` — SHA-256, top-1 + top-5 (golden + full), per-class accuracy, backbone + weights enum, freeze policy, env fingerprint.
- `app/classifier/eval/golden_images/` — 50 TIFFs.
- `app/classifier/eval/golden_expected.json` — labels + top-1 confidences.
- `app/classifier/eval/golden.py` — replay test (byte-identical labels, top-1 within 1e-6). **Fail blocks CI.**
- Boot-check helpers: `api` and `worker` refuse to start if weights missing, SHA mismatch, or top-1 below README threshold.

### Directories

`app/classifier/`, `app/classifier/models/`, `app/classifier/eval/`, `app/core/` (boot checks).

### Rules you must respect

- **No hardcoded secrets** — if you ever read a credential, it comes from Vault via Fakih's adapter.

### Use cases — what other people will expect from your code

**CLF-UC-1 — classify a document** *Who:* the inference worker (Nasser's code). *What they do:* call `classify(image_bytes)` with a TIFF's bytes. *What you must return:* a typed `Prediction` (label + top-5 + top-1 confidence). Same input → same output, deterministic. p95 latency < 1.0 s on CPU.

**CLF-UC-2 — make an annotated overlay** *Who:* the inference worker. *What they do:* call `make_overlay(image_bytes, prediction)`. *What you must return:* PNG bytes with the predicted label and confidence drawn on the image.

**CLF-UC-3 — refuse to start on bad weights** *Who:* `api` and `worker` lifespan code (Fakih + Nasser). *What they do:* call your three boot-check helpers (`verify_classifier_present`, `verify_classifier_sha`, `verify_classifier_top1_above_threshold`) at startup. *What you must do:* raise a clear error if weights are missing, SHA-256 doesn't match `model_card.json`, or model card's `test_top1` is below the README threshold (`MIN_MODEL_TOP1`). The container should exit with a readable log line, not a stack trace.

**CLF-UC-4 — golden replay test in CI** *Who:* GitHub Actions (Shari wires this). *What it does:* runs your `golden.py` against the 50 golden TIFFs. *What must pass:* every label byte-identical to `golden_expected.json` AND every top-1 confidence within 1e-6. Any drift = CI fail = merge blocked.

---

## API — Service Owner (Fakih)

### Tasks (brief)

- FastAPI app that authenticates users, enforces RBAC, queues classification jobs, exposes user/batch/prediction endpoints. **API never runs inference.**
- `fastapi-users` + JWT, email/password registration. JWT signing key from Vault.
- Casbin RBAC: admin / reviewer / auditor per the brief's matrix.
- Role-toggle endpoint: permissions update on next request (no logout/login) + audit row.
- `fastapi-cache2` (Redis) on `GET /me`, `GET /batches`, `GET /batches/{bid}`, `GET /predictions/recent`. **Invalidation in service layer only.**
- Audit log (actor, action, target, timestamp) on every role change, relabel, batch state change.
- Layered: routers HTTP-only, services own transactions + cache invalidation, repos SQL-only (no HTTPException, no cache), domain Pydantic distinct from ORM.

### Deliverables (brief)

- Endpoints: `/auth/*`, `GET /me`, `GET /batches`, `GET /batches/{bid}`, `GET /predictions/recent`, `PATCH /predictions/{pid}`, `GET /audit`, `POST /admin/users/invite`, `POST /admin/users/{id}/role`, `GET /health`.
- Three working roles, role-toggle with audit + Casbin reload, cache invalidation on every write touching a cached read.
- 401 / 403 / structured error envelope (no stack traces leaked).

### Directories

`app/api/`, `app/api/schemas/`, `app/services/`, `app/repositories/`, `app/domain/`, `app/db/`, `app/infra/casbin/`, `app/core/`, `alembic/versions/`, `tests/`.

### Rules you must respect

- Routers never touch SQLAlchemy, cache, or external systems.
- Repositories never raise HTTPException, never invalidate cache.
- **Cache invalidation lives only in services.**
- Domain Pydantic models stay distinct from SQLAlchemy ORM types.
- **401 if no/invalid token, 403 if role insufficient** — never mix the two.
- **Every state change writes an audit row** (role toggle, relabel, batch state).
- `request_id` **is set in middleware** and included in every log line — and injected into RQ job kwargs when handing off to the worker.
- **No hardcoded secrets** — JWT key and all DB/MinIO creds come from Vault at lifespan startup.

### Cross-track coordination (owned by Fakih)

- **Phase 1 — Monday:** repo skeleton, layered dirs, baseline tooling, structured logging, request-id middleware, empty Alembic migration, compose skeleton.
- **Phase 6 — Thursday:** integration, latency measurement, demo rehearsal, tag.
- **Trello (graded):** all 4 members, cards distributed, To Do → In Progress → Review → Done.
- **COLLABORATION.md:** Trello link + who owned what + merges + where stuck + one decision disagreed on.
- **Friday 20-min presentation rehearsal.**

### Use cases — every reviewer flow your API must satisfy

**API-UC-1 — register and log in** *Who:* a new user (or the frontend on their behalf). *What they do:* `POST /auth/register` then `POST /auth/jwt/login`. *What must happen:* account row created with hashed password (never plaintext); login returns a JWT with 30-min TTL.

**API-UC-2 — see who I am** *Who:* any authenticated user (frontend on every page load). *What they do:* `GET /me` with a valid Bearer token. *What must happen:* return `{ id, email, role }`. Response is cached (Redis); cache is keyed per-user so toggling one user's role doesn't pollute another's view.

**API-UC-3 — auth failures** *Who:* anyone hitting a protected endpoint. *What they do:* call it with no token, an expired token, or a token whose role isn't allowed for that endpoint. *What must happen:* **401 if no/invalid token, 403 if role insufficient**. Body is your structured error envelope with `request_id` — never a stack trace.

**API-UC-4 — list and read batches** *Who:* admin / reviewer / auditor (all three). *What they do:* `GET /batches` (paginated list) and `GET /batches/{bid}` (detail with all predictions for that batch). *What must happen:* both responses cached. Cache invalidated when the worker writes a new prediction into that batch (via API-UC-8) or when a reviewer relabels (via API-UC-5).

**API-UC-5 — reviewer relabels a low-confidence prediction** *Who:* reviewer (or admin). *What they do:* `PATCH /predictions/{pid}` with a new label. *What must happen:*
- If original `top1_confidence >= 0.7` → **409 Conflict** (the guard is in code, not docs).
- If caller is `auditor` → **403**.
- Otherwise: label updated, **audit row inserted** (`action=relabel`, actor=current user), batch cache + recent-predictions cache invalidated **by the service** (not the router).

**API-UC-6 — admin toggles a user's role** *Who:* admin. *What they do:* `POST /admin/users/{id}/role` with `{ "role": "reviewer" }`. *What must happen:* role updated, **audit row inserted**, Casbin enforcer reloaded (so policy reflects the change), target user's `/me` cache cleared. The affected user's permissions take effect on their **very next request** — no logout/login. If caller isn't admin → 403.

**API-UC-7 — read the audit log** *Who:* admin or auditor. *What they do:* `GET /audit?limit=&offset=`. *What must happen:* paginated rows (`actor`, `action`, `target_type`, `target_id`, `timestamp`). **403 if caller is a reviewer.**

**API-UC-8 — worker records a prediction** *Who:* the inference worker (Nasser's code) — not a user. *What they do:* call `prediction_service.record_prediction(batch_id, filename, prediction, overlay_minio_key, content_sha256, request_id)` after inference completes. *What must happen:* prediction row written; the affected batch's cache + `predictions:recent` cache invalidated by the service; if this prediction completes the batch, a batch-state audit row is written too.

---

## PIPE — Pipeline Owner (Nasser)

### Tasks (brief)

- SFTP polling worker: picks up files within 5 s, uploads to MinIO, enqueues RQ job.
- Inference worker: dequeues, runs `classify()`, writes prediction row via service, writes overlay PNG to MinIO, invalidates caches via service layer.
- Use **RQ (Redis Queue)**, not Celery.
- Worker refuses to start under same conditions as `api`.
- Structured JSON logs per worker job, with `request_id` propagating across api → queue → worker.

### Deliverables (brief)

- `sftp-ingest` container — polling entrypoint.
- `worker` container — RQ entrypoint, inference + overlay + prediction-row write + cache invalidation.
- **E2E:** SFTP drop → visible in `GET /batches/{bid}` p95 < 10 s (single-doc batch).
- **Inference p95 < 1.0 s on CPU.**
- Overlay PNGs in MinIO `overlays/`.
- Malformed inputs (zero-byte, non-image, oversized) quarantined to MinIO `failed/`, no prediction row.
- Idempotent on `(batch_id, filename, content_sha256)` — no duplicate rows.
- Structured JSON logs per worker job with the request id.

### Directories

`app/workers/`, `app/infra/` (sftp, minio, queue), `app/core/` (request-id), `tests/`.

### Rules you must respect

- **Every state change is written through `prediction_service.record_prediction(...)`** — never `INSERT` into `predictions` directly from worker code. The service writes the audit row and invalidates caches; you'd skip both if you bypassed it.
- `request_id` **propagates** — read it from RQ job kwargs, bind it to the structured logger before any work, include it in every log line.
- **No hardcoded secrets** — SFTP / MinIO / Redis credentials come from Vault via Fakih's adapter at lifespan startup.

### Use cases — what your two workers must guarantee

**PIPE-UC-1 — happy-path ingest** *Who:* the scanner (external; no user account). *What they do:* SFTPs a valid TIFF into the watched directory. *What must happen within 5 s:* `sftp-ingest` picks it up, uploads to MinIO `incoming/{batch_id}/{filename}`, generates a `request_id`, enqueues an RQ job carrying that `request_id` and the file's content hash.

**PIPE-UC-2 — malformed input is quarantined** *Who:* the scanner. *What they do:* drops a zero-byte file, a non-image (e.g. `.txt`), an oversized file (> 25 MB), or an unsupported extension. *What must happen:* file moves to MinIO `failed/{batch_id}/{filename}`, one structured log line records the reason, **no RQ job is enqueued**, **no prediction row is created**. The scanner never sees an error — quarantine is silent from their perspective.

**PIPE-UC-3 — happy-path inference** *Who:* the inference worker (your code). *What it does:* pulls an RQ job, fetches the object from MinIO, calls `classify(image_bytes)` (Saleh's code), calls `make_overlay(image_bytes, prediction)` (Saleh's code), uploads the overlay PNG to MinIO `overlays/{batch_id}/{filename}.png`, calls `prediction_service.record_prediction(...)` (Fakih's code). *What must happen:* end-to-end SFTP→`GET /batches/{bid}` p95 < 10 s for single-doc batches; inference itself p95 < 1.0 s on CPU.

**PIPE-UC-4 — idempotency** *Who:* anyone who re-enqueues the same job (or the same file dropped twice). *What happens:* job sees `(batch_id, filename, content_sha256)` already has a row → **no-op**, no duplicate prediction. The `predictions` table has a UNIQUE constraint on this triple; you handle the constraint-violation cleanly.

**PIPE-UC-5 — transient failure + retry** *Who:* the worker, when MinIO is briefly unreachable or `classify()` throws. *What happens:* RQ retries up to 3 times with exponential backoff (the `@retry` decorator). After 3 failures, the job lands in `failed_job_registry` AND a batch-state audit row is written (via `prediction_service`). Structured log records the chain of attempts.

**PIPE-UC-6 — request-id propagates everywhere** *Who:* a reader debugging "what happened to this file?" on Friday. *What they do:* grep logs for one `request_id`. *What must happen:* matches in `sftp-ingest`, in the RQ queue layer, and in the `worker` — same `request_id` in all three. The id is set when the file is first picked up; it travels in RQ job kwargs, and your worker re-binds it to the logger before any work begins.

**PIPE-UC-7 — worker refuses to start on bad weights** *Who:* the worker container's lifespan code. *What it does:* calls Saleh's boot-check helpers (`verify_classifier_present`, `verify_classifier_sha`, `verify_classifier_top1_above_threshold`) before binding to the queue. *What must happen:* container exits nonzero with a clear log line if any check fails. Same behavior as `api`.

---

## INFRA — Infrastructure + UI Owner (Shari)

### Infrastructure — Tasks (brief)

- Compose: `api`, `worker`, `sftp-ingest`, `migrate`, `db` (postgres:16), `redis` (redis:7), `minio`, `sftp` (atmoz/sftp), `vault` (hashicorp/vault dev mode).
- `migrate` runs `alembic upgrade head` and exits before `api` boots.
- All secrets resolve from Vault at startup. `grep -ri 'password' app/` returns zero matches outside Vault-reading code.
- `api` refuses to boot if Vault unreachable or Casbin policy table empty.
- `cp .env.example .env && docker compose up` from a fresh clone brings the stack up. `.env` = Vault root token + ports only.
- CI on every push: lint, type-check, build app image, golden test, full-stack smoke test (SFTP → prediction in API).
- Latency budgets in README and demoed: cached < 50 ms p95, uncached < 200 ms p95, inference < 1.0 s p95, e2e < 10 s p95.
- Tag `v0.1.0-week6`.

### Infrastructure — Deliverables (brief)

- `docker-compose.yml` (9 services), single `Dockerfile` with 4 entrypoints.
- `.env.example`, gitignored `.env`.
- Alembic config + migrations.
- Vault seed step (script or init container) writing JWT key + Postgres/MinIO/SFTP creds idempotently.
- GitHub Actions: ruff + mypy + pytest + golden + smoke + grep gate.
- `ARCH.md`, `DECISIONS.md`, `RUNBOOK.md`, `SECURITY.md`, `LICENSES.md`, repo `README.md`.
- `v0.1.0-week6` tag on the CI-green merge commit.

### Infrastructure — Rules you must respect

- **One backend image, four entrypoint commands** (api, worker, sftp-ingest, migrate) — not four Dockerfiles. Frontend has its own separate Dockerfile.
- **No hardcoded secrets in compose or `.env`** — `.env` carries only the Vault root token and ports. Everything else is seeded into Vault by the `seed-vault` step.
- **CI enforces the grep gate** — any commit with `password = "..."` in `app/` (outside `app/infra/vault.py`) fails CI before merge.

### UI — Tasks (team-added, not in brief)

- Vite + React + TypeScript app in `frontend/`.
- Login page (`POST /auth/jwt/login`), session stored as JWT, sent as `Authorization: Bearer <token>` on every request.
- Role-aware layout shell: nav items shown/hidden based on the logged-in user's role.
- Pages for every API capability:
  - `/me` — current user (id, email, role).
  - `/batches` — paginated batch list.
  - `/batches/:id` — batch detail with predictions, overlay images.
  - Relabel modal on a prediction (reviewer-only; disabled when top-1 ≥ 0.7).
  - `/admin/users` — admin invite + role toggle (admin-only).
  - `/audit` — audit log table (admin + auditor).
- Handle 401 → redirect to login; 403 → friendly "not allowed" message.

### UI — Deliverables

- Working frontend that exercises every API endpoint.
- Dockerfile for `frontend/` (nginx serving the built static bundle).
- Frontend service added to `docker-compose.yml`.
- Compose up brings up frontend on a documented port (e.g., `:5173`); README explains how to access.

### UI — Rules you must respect

- **401 vs 403** — 401 clears the token and redirects to login; 403 shows the "not allowed" page. Don't conflate them.
- **No hardcoded API URLs or tokens** — read the API base URL from a Vite env var (`VITE_API_BASE_URL`), never inline a string.

### Directories

Repo root (`docker-compose.yml`, `Dockerfile`, `.env.example`, `.gitignore`, `.gitattributes`, `pyproject.toml`, `uv.lock`, lint configs, READMEs), `alembic/`, `scripts/`, `app/infra/` (Vault adapter), `app/core/` (config, logging), `.github/workflows/`, `frontend/` (Vite app + Dockerfile).

### Use cases — INFRA — what the platform must do for anyone touching it

**INFRA-UC-1 — fresh-clone bring-up** *Who:* a new developer or the Friday reviewer. *What they do:* `git clone … && cd … && cp .env.example .env && docker compose up`. *What must happen:* in under ~90 s, the full stack is healthy — `migrate` ran and exited, `seed-vault` wrote secrets, `api` is responding to `GET /health`, `worker` and `sftp-ingest` are running, `frontend` is reachable. No extra manual step.

**INFRA-UC-2 — boot ordering is correct** *Who:* compose itself. *What it must do:* `migrate` waits for `db` healthy → runs `alembic upgrade head` → exits 0. `seed-vault` waits for `vault` healthy → writes secrets → exits 0. `api` waits for `migrate completed_successfully` + `seed-vault completed_successfully` + redis/minio/vault healthy. `worker` and `sftp-ingest` wait for `api` healthy.

**INFRA-UC-3 — secrets resolve from Vault** *Who:* any backend container needing a credential (JWT key, Postgres pw, MinIO creds, SFTP creds). *What it does:* reads the secret from Vault (KV v2 mount `secret/`) at startup, via Fakih's Vault adapter in `app/infra/vault.py`. *What must hold:* nothing is hardcoded in code or compose. `.env` carries only the Vault root token and ports — never the actual secrets.

**INFRA-UC-4 — kill-Vault demo** *Who:* the Friday reviewer says "stop Vault, restart api". *What must happen:* `docker compose stop vault && docker compose restart api` makes `api` exit nonzero with a clear log line ("Vault unreachable, refusing to start"). This is the brief's "secrets discipline" gate.

**INFRA-UC-5 — secrets grep gate** *Who:* the Friday reviewer. *What they do:* `grep -ri 'password' app/`. *What must happen:* no matches outside `app/infra/vault.py`. CI enforces the same — any commit that introduces a hardcoded password fails the lint job before merge.

**INFRA-UC-6 — CI gate on every push** *Who:* any developer pushing to a branch or opening a PR. *What happens:* GitHub Actions runs lint + type-check + image build + Saleh's golden test + a smoke test (compose up → SFTP drop → poll `/batches/{bid}` until prediction appears, with timeout). Any failure blocks merge.

**INFRA-UC-7 — docs that stand alone** *Who:* a teammate or reviewer reading the repo for the first time. *What they expect:* each of `ARCH.md`, `DECISIONS.md`, `RUNBOOK.md`, `SECURITY.md` answers its own question without forcing them into the code.
- `ARCH.md` — layer diagram + one full walkthrough of `PATCH /predictions/{pid}` through router → service → repo → DB.
- `DECISIONS.md` — non-obvious choices (Tiny vs Small, TTLs, JWT TTL, no refresh tokens, no HTTPS, RQ over Celery, why one image with 4 entrypoints).
- `RUNBOOK.md` — gets the stack running, runs the demo steps, measures latency, kills Vault for the demo.
- `SECURITY.md` — secrets posture, grep gate, JWT TTL, rate limits, what's intentionally out of scope.

### Use cases — UI — what the UI must do for each role

**UI-UC-1 — anyone logs in** *Who:* a registered user. *What they do:* enter email + password on the login page → submit. *What must happen:* call `POST /auth/jwt/login`, store the JWT, redirect to `/me`. Bad creds show an inline error, not a navigation.

**UI-UC-2 — JWT carried on every request** *Who:* the frontend's API client. *What it must do:* attach `Authorization: Bearer <token>` to every API request. If the API returns 401 (expired/missing token) → clear the token and redirect to login.

**UI-UC-3 — role-aware navigation** *Who:* any logged-in user. *What they see:* nav items reflect their role.
- **Admin** sees: `/me`, `/batches`, `/admin/users`, `/audit`.
- **Reviewer** sees: `/me`, `/batches` (and the relabel modal on predictions where confidence < 0.7).
- **Auditor** sees: `/me`, `/batches`, `/audit`. If a reviewer manually types `/admin/users` in the URL: show the "not allowed" page (403 fallback), don't crash.

**UI-UC-4 — view batches** *Who:* any authenticated user. *What they do:* click "Batches". *What must happen:* page calls `GET /batches`, renders a paginated table. Clicking a row opens `/batches/:id`, which calls `GET /batches/{bid}` and shows each prediction with its overlay image (PNG fetched via the API/MinIO presigned URL).

**UI-UC-5 — reviewer relabels a low-confidence prediction** *Who:* reviewer. *What they do:* on `/batches/:id`, click the "Relabel" button on a prediction. *What must happen:* button is **disabled with a tooltip** when `top1_confidence >= 0.7` (the UI enforces the same guard the API enforces). When enabled, the modal opens, the reviewer picks the new label, submit → `PATCH /predictions/{pid}` → close modal → refresh the row. If the API returns 409 (confidence guard server-side), show the message inline.

**UI-UC-6 — admin toggles a user's role** *Who:* admin. *What they do:* on `/admin/users`, change a user's role in a dropdown. *What must happen:* call `POST /admin/users/{id}/role`. On success, the affected user's next request reflects the new role with no logout/login — demo path: have the affected user keep the app open in another tab, toggle their role, watch their nav update on next page change.

**UI-UC-7 — auditor reads the audit log** *Who:* admin or auditor. *What they do:* navigate to `/audit`. *What must happen:* call `GET /audit?limit=&offset=`, render a paginated table (actor email, action, target, timestamp). Reviewer who manually navigates here → 403 fallback page.

**UI-UC-8 — graceful errors** *Who:* any user. *What must happen:*
- **401** → token cleared, redirect to login.
- **403** → friendly "you don't have permission for this" page, with a link back.
- **Network error / API down** → toast or banner, no white screen.
- **API 5xx** → "something went wrong, try again" toast.
