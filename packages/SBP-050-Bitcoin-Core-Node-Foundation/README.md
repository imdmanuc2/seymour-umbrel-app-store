# SBP-050 — Bitcoin Core Node Foundation

Replaces the original `seymour-bitcoin-node` nginx placeholder with the
foundation for a Seymour-managed Bitcoin Core runtime.

## Foundation

- Bitcoin Core 29.0.0
- amd64 / arm64 image definition
- persistent node data
- generated bitcoin.conf
- mainnet/regtest/testnet4 network selection
- guarded RPC credentials
- P2P and ZMQ configuration
- node healthcheck
- read-only status service
- canonical Seymour runtime state
- Bitcoin runtime contract

Provider:

`bitcoin-mainnet`

App:

`seymour-bitcoin-node`

Image:

`ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0`

SBP-050 installation changes repository source only. It does not start
Bitcoin Core, modify blockchain data, or execute lifecycle operations.
