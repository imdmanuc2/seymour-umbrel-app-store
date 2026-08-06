# SBP-010 — Guarded Blockchain Lifecycle Actions

Adds guarded start, stop, restart, and state-refresh operations to the Seymour Blockchain Manager.

## Adds
- server-side lifecycle action API
- confirmation-token enforcement
- provider/app allow-list validation
- existing Umbrel control bridge integration
- append-only lifecycle evidence
- post-action state verification
- UI confirmation flow

No live app is restarted during installation or verification.
