# SBP-004 — Umbrel Runtime Integration

Adds the shared Seymour runtime bridge for Umbrel.

## Adds

- installed-app discovery
- app-source discovery
- Docker container inspection
- normalized app lifecycle status
- version discovery
- dependency reporting
- log collection
- health-endpoint probing
- JSON runtime API
- CLI diagnostics
- reusable runtime contract for future Seymour apps

## Safety

SBP-004 is read-only. It does not install, start, stop, restart, remove, update,
or modify any Umbrel app, container, firewall rule, blockchain, or host setting.

## Workflow

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```
