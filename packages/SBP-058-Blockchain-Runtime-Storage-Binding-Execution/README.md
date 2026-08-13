# SBP-058 — Blockchain Runtime Storage Binding Execution

Connects selected storage targets to the actual host-side blockchain data bind.

Adds:
- `SEYMOUR_BLOCKCHAIN_DATA_PATH` support in BTC/BCH Compose
- installer-side storage binding execution
- selected storage path propagated into the install environment
- post-install Docker mount-source verification

Package install/verify are non-destructive and do not restart runtimes or move chain data.
