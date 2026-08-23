# SBP-075.1 — Canonical Runtime Binding Contract

Defines the canonical persisted storage-binding contract used by
Seymour-managed blockchain runtimes.

Supported layouts:

- `single-path`
  - Bitcoin
  - Monero
  - future runtimes whose entire blockchain data directory resides on
    one storage target

- `hybrid-blocks`
  - Bitcoin Cash when only the blocks directory resides on remote
    bulk storage

This package introduces the shared contract only.

It does not:

- migrate existing runtimes
- restart containers
- modify installed compose files
- change existing runtime bindings
