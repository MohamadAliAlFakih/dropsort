# Architecture decisions (dropsort)

## How to use this file

Short entries: **context**, **decision**, **consequences**. Add new rows as the project stabilizes. Use `TODO(team)` when a decision is still open.

---

### ADR-001 — Frontend stack

- **Context:** Need a small, standard SPA for the Week 6 UI track.
- **Decision:** Use **React + Vite + TypeScript**; no global state library in the initial scaffold; **React Router** for navigation.
- **Consequences:** Simple mental model; state for auth can stay local/context until requirements grow.

---

### ADR-002 — Frontend production delivery

- **Context:** API and UI are separate processes; production should be small and cache-friendly.
- **Decision:** **Multi-stage Docker** for `frontend/`: Node builds static assets; **nginx** serves `dist/` on container port **80**.
- **Consequences:** `VITE_API_BASE_URL` is applied at **image build** time (Vite behavior). Runtime URL changes require a rebuild or a future runtime-config pattern.

---

### ADR-003 — API base URL from environment

- **Context:** Avoid hardcoding API origins per environment.
- **Decision:** Use **`VITE_API_BASE_URL`** for browser calls; validate presence in the API client module.
- **Consequences:** Compose/CI must pass build args for the frontend image; browser origin vs API origin must satisfy CORS on the API (`TODO(team):` CORS policy owner).

---

### ADR-004 — Open items (not decided here)

- `TODO(team):` JWT storage strategy beyond local scaffold (cookies vs localStorage) once fastapi-users flow is fixed.
- `TODO(team):` whether compose uses a reverse proxy in front of api + frontend.
- `TODO(team):` golden-set threshold and model artifact layout (classifier track).