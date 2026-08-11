# SBP-044 — Operations Evidence Timeline & Request Resilience

Frontend-only Operations Center hardening and evidence UX.

Primary repair:
- no Operations request may leave the UI stuck indefinitely on "Planning..."
- all fetches use an explicit timeout
- timeout/network/HTTP failures are rendered inside the Operations surface
- lifecycle planning still uses only POST /api/lifecycle/operation
- no lifecycle action is executed by verify.sh

Evidence UX:
- lifecycle history renders as a timestamped timeline
- diagnostics render as structured result cards when possible
- logs render in a dedicated monospace viewer
- raw JSON remains available in the Evidence output panel
- successful lifecycle plans refresh history automatically
- operation status remains tied to canonical runtime state

This package does not change backend APIs, runtime-state normalization, or lifecycle policy.
