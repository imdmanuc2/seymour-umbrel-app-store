# SBP-009 — Blockchain Manager Live Dashboard

Adds live read-only host and Bitcoin Cash telemetry to the Seymour Blockchain
Manager.

## Adds

- host CPU, memory, storage, architecture, and Docker status;
- BCH container and RPC health;
- BCH height, headers, sync progress, peers, mempool, and disk usage;
- auto-refreshing UI;
- installed, running, syncing, stopped, and error states;
- sync and disk progress bars;
- safe read-only status routes;
- planned providers remain locked;
- no lifecycle execution yet.

## Run

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```

No container image is published and no live Umbrel app is restarted.
