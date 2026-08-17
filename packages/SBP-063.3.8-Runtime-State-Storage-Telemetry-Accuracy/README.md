# SBP-063.3.8 — Runtime State & Storage Telemetry Accuracy

Repairs two Blockchain Manager projection errors without modifying live blockchain runtimes:

1. Definitive installed/stopped runtime state overrides stale RPC/sync telemetry and clears UI grace state.
2. BCH chain-data usage reports the runtime footprint rather than whole-filesystem usage. The footprint is cached and hybrid-storage aware: local `/node-data` is measured without crossing filesystems, while `/node-data/blocks` is measured separately and added once.

The package updates repository source plus the installed Blockchain Manager and BCH status-service source. It does **not** restart Blockchain Manager, the BCH node, the BCH status service, or Bitcoin. After verification, restart Blockchain Manager and the BCH **status service only** to load the new code.
