
---

## `SECURITY.md`

**Purpose:** Threats and practices at a level appropriate for a course project; references brief expectations without claiming they are already enforced in code.

```markdown
# Security (dropsort)

## Scope

Security expectations for the Week 6 submission: secrets handling, access control, and operational hygiene. This document does **not** replace a full production threat model.

## Threat model (summary)

- **Asset:** Document images, classification results, audit log, credentials.
- **Adversaries:** Curious insiders, mistaken public exposure of dev ports, compromised dev laptops.
- **Out of scope:** Nation-state attackers; production multi-tenant hardening.

## Secrets

- **Vault:** Project brief requires secrets to resolve from **HashiCorp Vault** for backend services. `TODO(team):` document KV version, paths, and seed procedure.
- **Repository:** No long-lived production secrets committed. `TODO(team):` maintain grep/CI checks per brief (e.g. no passwords in `app/` outside Vault integration).
- **Frontend:** Only **public** build-time variables (e.g. `VITE_API_BASE_URL`) belong in the SPA bundle. Never embed signing keys or database passwords in frontend env vars.

## Authentication and RBAC

- **Authentication:** Intended **JWT** via **fastapi-users** (`TODO(team):` endpoints and cookie/header strategy).
- **RBAC:** **Casbin** with admin / reviewer / auditor roles (`TODO(team):` policy storage and enforcement points).
- **Frontend:** Stores bearer token only via the scaffold’s local mechanism until login is wired; revisit storage and XSS implications when real auth ships.

## Transport and exposure

- Local compose binds services to host ports; do not forward those ports on untrusted networks without understanding the risk.
- `TODO(team):` TLS termination story if anything beyond localhost is used.

## Dependency and supply chain

- Pin images and lockfiles where possible (`TODO(team):` policy for backend `uv.lock` and frontend lockfile).
- Frontend production image uses official **Node** and **nginx** bases; rebuild on base image updates.

## Incident response (course scale)

If a dev token or test password leaks: rotate Vault dev data, rotate compose dev credentials, and force-push is **not** required for local-only tokens—coordinate with team lead.

## References

- [RUNBOOK.md](./RUNBOOK.md) — operational steps.
- [LICENSES.md](./LICENSES.md) — dataset and third-party terms.