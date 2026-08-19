# SBP-071 — Monero Multi-Arch Runtime Image Foundation

Creates the production image build/publish foundation for the Seymour Monero node.

Target image:

`ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1`

Platforms:

- linux/amd64
- linux/arm64

The GitHub workflow downloads the official Monero 0.18.5.1 CLI archives,
verifies the official SHA256 digest for each Linux architecture, stages only
`monerod`, builds architecture-specific GHCR tags, verifies `monerod --version`,
and publishes the canonical multi-architecture manifest only after both builds
succeed.

This package does not activate Monero in the provider catalog and does not install,
start, stop, restart, recreate, update, or uninstall any blockchain runtime.
