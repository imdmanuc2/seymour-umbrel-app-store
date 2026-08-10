# SBP-036.1 — Blockchain Manager Runtime Integration & Deployment Repair

Purpose: repair and verify the runtime deployment boundary discovered after SBP-036.

This package does not add a lifecycle implementation. It repairs the Blockchain Manager
container wiring required for the already-installed SBP-036 HTTP adapter to import the
canonical shared lifecycle stack.

Repairs:
- adds `SEYMOUR_PLATFORM_ROOT: /seymour-platform`
- adds lifecycle audit/evidence environment paths if missing
- adds the read-only shared mount:
  `/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro`

Safety:
- no Docker lifecycle commands
- no live Umbrel lifecycle action from doctor/install/verify
- `docker` is used only for read-only runtime inspection in verify.sh
- install.sh creates a timestamped backup
- rollback.sh restores the latest SBP-036.1 backup

After install, restart Blockchain Manager using the canonical native Umbrel lifecycle bridge:

    cd /home/umbrel/seymour-umbrel-app-store-git
    ./scripts/seymour-umbrel-app restart seymour-blockchain-manager \
      --execute --confirm RESTART-seymour-blockchain-manager

Then run:

    ./packages/SBP-036.1-Blockchain-Manager-Runtime-Integration-Deployment-Repair/scripts/verify.sh

