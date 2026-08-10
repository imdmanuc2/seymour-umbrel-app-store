# SBP-037 — Canonical Runtime State Reconciliation

SBP-037 removes the BCH lifecycle state split discovered during SBP-036.3.

Configured Seymour provider apps use the canonical `runtimeState` from their
existing status endpoint. BCH is wired through the already-present
`BCH_APP_ID` and `BCH_STATUS_URL` environment variables.

For configured provider apps:
- canonical `runtimeState` is authoritative
- missing/unreachable/invalid canonical state resolves to `unknown`
- there is no Docker/container-health inference fallback

For apps without a configured canonical provider endpoint:
- the existing native Umbrel lifecycle state adapter remains available

Canonical runtime states:
`starting`, `syncing`, `running`, `degraded`, `stopped`, `offline`, `error`, `unknown`.

No live lifecycle write is executed by doctor/install/verify.
