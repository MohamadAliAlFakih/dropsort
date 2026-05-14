# Collaboration (dropsort)

## Trello board

The team maintains a **Trello** (or equivalent) board for backlog and sprint status. Add the **public or invite link** in the course submission portal when required; it is intentionally not hardcoded in the repo so the link can rotate per term.

## Team roster

| Name | Focus |
|------|--------|
| Fakih (MA) | Course / coordination |
| Nasser | _(role per sprint)_ |
| Saleh | Classifier, model card, golden set |
| Shari | Infra, Compose, CI, frontend packaging |

GitHub handles: add in the submission metadata as required by instructors.

## Work ownership (high level)

| Area | Primary | Notes |
|------|---------|--------|
| Infra / Compose / CI / smoke | Shari | `docker-compose.yml`, `scripts/vault-seed.sh`, `scripts/ci_smoke.sh`, `.github/workflows/ci.yml`, nginx frontend image |
| API / services / repositories | Group | FastAPI + Casbin + Vault integration |
| Workers / pipeline | Group | SFTP ingest, browser upload → MinIO → RQ → `record_prediction` |
| Classifier / golden | Saleh | `classify.py`, weights, `golden.py`, boot checks |

## How we merge and review

- **Branches:** feature branches off the shared integration branch (e.g. `infra-ui` / main per team agreement); small PRs preferred.
- **Review:** at least one reviewer for non-trivial changes; infra/CI changes should be exercised locally or via CI before merge.
- **Conflicts:** resolve with rebase when linear history is needed for CI or release tags.

## Where we got stuck

Document one real blocker per milestone (e.g. Vault empty on first boot, Redis cache invalidation from workers, Git LFS on CI runners) and the fix — keeps demo Q&A short.

## Presentation prep

Agree verbally who covers: Compose bring-up, SFTP vs browser upload, RBAC demo, CI failure injection (e.g. golden or smoke), and collaboration tooling.
