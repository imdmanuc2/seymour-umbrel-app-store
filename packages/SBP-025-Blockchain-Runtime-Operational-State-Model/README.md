# SBP-025 — Blockchain Runtime Operational State Model

Defines one normalized operational state model for blockchain runtimes:
not-installed, stopped, starting, syncing, healthy, degraded.

It wires the normalized state into the BCH runtime API and Nexus registration payload.
No live restart is executed automatically.
