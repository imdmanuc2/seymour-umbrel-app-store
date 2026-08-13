# SBP-056 — Blockchain Storage Binding Plan

Connects a selected SBP-055 storage target to a provider-specific blockchain data path
without yet changing mounts or moving live chain data.

Adds:
- canonical provider -> storage directory naming
- storage binding plan contract
- safe destination path construction
- eligibility checks for local / attached / remote targets
- explicit runtimeHost vs storageTarget metadata
- deterministic data path such as:
  `<selected-target>/seymour-data/bitcoin-mainnet`

This package is intentionally non-destructive. It does NOT:
- mount NFS/SMB
- create host bind mounts
- move existing BTC/BCH data
- restart a blockchain runtime
- modify Umbrel app state

SBP-057 can use this contract to materialize the selected target on an Umbrel runtime host.
