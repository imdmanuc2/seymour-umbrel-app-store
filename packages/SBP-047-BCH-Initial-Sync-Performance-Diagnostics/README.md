# SBP-047 — BCH Initial Sync Performance Diagnostics

Observation-only instrumentation to explain BCH IBD performance before tuning.

Measures sync throughput, peer quality, Docker Engine container CPU/memory/block I/O, chain growth, ETA, and likely bottleneck. Short-window samples are stored in memory only. No BCH configuration, peers, or lifecycle actions are changed.
