# SBP-003 — BCH Fresh Sync Provisioning

Adds an executable **fresh-sync configuration workflow** to the Seymour
Bitcoin Cash Node app source.

## Adds

- persisted provisioning state
- generated RPC credentials
- fresh-sync configuration generation
- storage requirement checks
- sync readiness endpoint
- provisioning status endpoint
- first-run initialization behavior
- source-only verification and rollback

## Important

SBP-003 updates App Store source only. It does not install the Umbrel app,
start containers, expose RPC externally, or begin a blockchain sync by itself.

## Workflow

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```
