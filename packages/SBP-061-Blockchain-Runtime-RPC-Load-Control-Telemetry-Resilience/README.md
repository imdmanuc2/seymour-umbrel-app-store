# SBP-061 — Blockchain Runtime RPC Load Control & Telemetry Resilience

Addresses BCH RPC saturation and dashboard sync flapping with:
- process-wide 30-second BCH runtime cache
- single-flight probe coalescing
- last-known-good sync continuity
- explicit telemetry freshness metadata
- source-to-installed Blockchain Manager synchronization

No BCH restart and no blockchain-data modification occurs during install.
