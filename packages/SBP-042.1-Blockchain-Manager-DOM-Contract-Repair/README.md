# SBP-042.1 — Blockchain Manager DOM Contract Repair

Repairs the frontend crash introduced by SBP-042.

Root cause:
- SBP-042 replaced the old catalog summary cards.
- `loadCatalog()` still wrote to `providerCount`, `liveCount`, and `plannedCount`.
- Those elements no longer exist.
- `document.getElementById(...).textContent = ...` therefore threw and stopped
  the entire boot/render sequence.

This patch:
- removes the obsolete summary writes from `loadCatalog()`
- makes catalog status rendering null-safe
- adds a reusable `setText()` helper for non-critical DOM projections
- updates host metrics to use the safe helper
- preserves SBP-041 stabilization and SBP-042 operational-first UX
- does not modify backend APIs or lifecycle behavior
