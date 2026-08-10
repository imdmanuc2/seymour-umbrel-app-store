# SBP-036 — Blockchain Manager HTTP Lifecycle Route Integration

Binds the SBP-035 lifecycle API/frontend contract into the existing Seymour Blockchain Manager `ThreadingHTTPServer` application without introducing another lifecycle executor.

Adds:

- `POST /api/lifecycle/operation` — canonical lifecycle plan/execute request.
- `GET /api/lifecycle/history` — canonical append-only lifecycle audit history.
- compatibility handling for existing `POST /api/lifecycle/<action>` callers.
- a lazy lifecycle HTTP adapter that fails closed with HTTP 503 when canonical lifecycle transport is unavailable.
- a read-only mount of the repository `shared/` package into the Blockchain Manager container.

No direct Docker lifecycle is introduced. `verify.sh` does not perform a live Umbrel lifecycle action.

The native Umbrel bridge remains the sole lifecycle authority. The HTTP layer only adapts requests and responses.
