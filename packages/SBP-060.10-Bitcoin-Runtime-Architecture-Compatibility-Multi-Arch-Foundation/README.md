# SBP-060.10 — Bitcoin Runtime Architecture Compatibility & Multi-Arch Image Foundation

Adds fail-closed architecture compatibility checks for the Seymour Bitcoin runtime.

Observed live failure:
- runtime host: aarch64 / arm64
- image: ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0
- local image architecture: amd64
- result: exec format error

This package:
- adds architecture normalization and local Docker image inspection
- adds a guarded Bitcoin architecture preflight CLI
- adds `runtime-image-architecture-mismatch` to self-healing/recovery
- blocks Bitcoin install/start via the managed-runtime wrapper when the image is incompatible
- documents the required multi-arch image publishing contract: linux/amd64 + linux/arm64
- does not restart any blockchain runtime and does not modify blockchain data
