# Security (dropsort)

## Scope

Security expectations for the Week 6 submission: **secrets handling**, **access control**, and **operational hygiene**. This is not a full production threat model.

## Threat model (summary)

- **Assets:** Document images, classification results, audit log, credentials, model weights.
- **Adversaries:** Curious insiders, accidental exposure of dev ports on shared networks, compromised dev laptops.
- **Out of scope:** Nation-state attackers; multi-tenant SaaS hardening.

## Secrets

- **Vault (required for API/worker):** All database, JWT, MinIO, and SFTP credentials used by the Python services are read at process startup from **HashiCorp Vault KV v2** (`secret/…`) via `app/core/vault.py`. The API **refuses to start** if Vault is unreachable (**BOOT-01**).
- **Compose file:** Contains **only development defaults** (e.g. Postgres superuser password for the DB container, MinIO dev keys) so containers can become healthy. These are **not** imported into `app/` as literals for production paths.
- **Repository policy:** CI runs a **grep gate** blocking the literal string `password` anywhere under `app/` except the canonical Vault module (`vault.py`), to discourage accidental secret commits.
- **Frontend bundle:** May contain **`VITE_API_BASE_URL`** (public). It must **never** contain DB passwords, JWT signing keys, or Vault tokens.

## Authentication and RBAC

- **Authentication:** **JWT** via **fastapi-users** — `POST /auth/jwt/login` returns a bearer token.
- **RBAC:** **Casbin** enforces `(role, resource, method)` tuples stored in PostgreSQL. The API **refuses to start** if the Casbin table is empty (**BOOT-02**).
- **Client storage:** The SPA keeps the bearer token in **memory/local storage** (see frontend auth module); treat XSS as in scope for reviewer threat when demoing on untrusted machines.

## Classifier integrity

- **Weights:** Shipped under `app/classifier/models/` with **`model_card.json`** recording **`weights_sha256`**. API and inference worker **refuse to start** on missing files or SHA mismatch (**BOOT-03**).
- **Regression:** If **`MIN_MODEL_TOP1`** is set in the environment, **`metrics.test_top1`** in the model card must meet or exceed it (**BOOT-04**); otherwise the check is skipped for frictionless local dev.

## Transport and exposure

- Default Compose **binds to localhost-facing ports** on the host. Do not expose those ports on untrusted networks without TLS and authentication review.
- There is **no TLS** inside the dev stack; production would terminate TLS at an edge proxy.

## Dependency and supply chain

- Backend: **`uv.lock`** pins Python dependencies.
- Frontend: **`package-lock.json`** pins npm dependencies.
- Container bases: official **python**, **postgres**, **redis**, **hashicorp/vault**, **minio**, **nginx**, **node** images — rebuild periodically for upstream CVEs.

## Incident response (course scale)

If a dev token leaks: rotate Vault dev data and compose defaults; coordinate with the team lead. For local-only secrets, force-push is usually unnecessary.

## References

- [RUNBOOK.md](./RUNBOOK.md) — operational steps and smoke test.
- [LICENSES.md](./LICENSES.md) — dataset and third-party terms.
