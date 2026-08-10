# SBP-035 — Lifecycle API / Frontend Contract Integration

Adds a thin frontend/API contract over the canonical SBP-034 lifecycle Operations facade.

## Scope

- Adds `shared/app_lifecycle/api.py`.
- Exposes camelCase frontend-safe operation and history envelopes.
- Extends the canonical SBP-032 result projection to carry the existing SBP-031 confirmation token instead of re-deriving it in the API layer.
- Adds versioned lifecycle API contract metadata.
- Does **not** add a second execution path.
- Does **not** directly execute Docker lifecycle.
- Does **not** bind HTTP routes yet; route binding remains a separate installable milestone so the Blockchain Manager web runtime can be integrated and restarted independently.

## Safety

Planning remains the default. Write execution is still owned by `LifecycleExecutor` and requires the canonical confirmation token.
