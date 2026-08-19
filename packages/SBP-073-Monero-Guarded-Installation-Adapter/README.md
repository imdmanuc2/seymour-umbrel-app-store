# SBP-073 — Monero Guarded Installation Adapter

Adds first-class guarded installation support for the Monero provider.

## Contracts

- Monero uses the verified canonical production image.
- Installation uses the provider-neutral Blockchain Manager installer.
- Installation requires `INSTALL-seymour-monero-node`.
- Monero RPC authentication remains `none`.
- Runtime storage is persisted before Umbrel installation/start.
- Runtime DNS identities are materialized by the app pre-install hook.
- Monero becomes selectable after adapter promotion.
- This package does not install or start Monero.
- Existing Bitcoin and Bitcoin Cash runtimes are not modified.
