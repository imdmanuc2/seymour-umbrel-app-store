# SBP-063.3.10 — Recovery Evidence & Cleanup Policy

Purpose: provide a guarded, auditable cleanup workflow for BCH recovery datasets created during hybrid-storage repair.

This package does not modify the running BCH or Bitcoin runtimes.

Recovery set:
- Local:  /home/umbrel/umbrel/app-data/seymour-bch-node/data/node/recovery-20260818-000411
- Remote: /mnt/seymour-storage/bitcoin-cash-mainnet/recovery-20260818-000411

Required confirmation:
DELETE-BCH-RECOVERY-20260818-000411

Safety gates:
- BCH node must be running and healthy.
- BCH restart count must remain 0.
- Bitcoin node must be running and healthy.
- Live BCH /data/blocks must still be bound to /mnt/seymour-storage/bitcoin-cash-mainnet/blocks.
- Both recovery directories must exist for execute mode.
- Evidence is written before and after cleanup.
