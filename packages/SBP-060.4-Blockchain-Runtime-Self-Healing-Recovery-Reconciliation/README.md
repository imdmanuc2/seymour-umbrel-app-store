# SBP-060.4 — Blockchain Runtime Self-Healing & Recovery Reconciliation

Provider-neutral, bounded recovery foundation for Seymour blockchain runtimes.

Safe recovery flow:
Detect -> classify -> plan -> approved repair -> verify -> evidence.

Covers the failure classes encountered during BCH/BTC recovery:
- missing local/attached storage mount
- missing NFS mount
- nested bind mount hidden by NFS export configuration
- storage binding mismatch
- Docker DNS alias collision
- startup warmup / RPC -28 classification
- existing chain data with missing runtime registration
- suspicious fresh sync when a large external chain already exists

This package does not format disks, delete chain data, reindex/resync automatically,
change ownership recursively, or move large blockchain datasets.
