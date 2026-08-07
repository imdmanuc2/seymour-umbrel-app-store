# SBP-020 — BCH Runtime Health & RPC Detection

Fixes false BCH not-installed/docker-unavailable classification by directly probing the mounted Docker socket and separating container state from RPC health. Adds GET /api/runtime/bch-health and normalizes BCH state in Nexus registration payloads.
