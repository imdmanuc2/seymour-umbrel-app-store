# SBP-025 v2 — Blockchain Runtime Operational State Model

Compatibility-corrected package for repositories that already include SBP-020 through SBP-024.

Defines normalized runtime states:
- not-installed
- stopped
- starting
- syncing
- healthy
- degraded

The package is idempotent and understands the current SBP-020 Nexus registration wrapper.
No live restart is executed automatically.
