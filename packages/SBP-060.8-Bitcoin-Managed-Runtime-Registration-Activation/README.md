# SBP-060.8 — Bitcoin Managed Runtime Registration & Activation

Adds the guarded workflow needed to make `seymour-bitcoin-node` a first-class
managed runtime in Seymour Blockchain Manager.

This package does **not** install or start Bitcoin during package installation.

It installs a provider-aware control script that:

1. verifies the Bitcoin provider/app definition exists
2. verifies the selected Bitcoin data path is mounted and writable
3. plans native Umbrel installation/registration
4. executes native Umbrel installation only with explicit confirmation
5. persists the selected Bitcoin blockchain-data path into installed Compose
6. plans native Umbrel start
7. executes start only with explicit confirmation
8. relies on SBP-060.7 pre-start storage protection
9. emits structured evidence

Default managed Bitcoin data path:
`/mnt/seymour-storage/bitcoin-mainnet`
