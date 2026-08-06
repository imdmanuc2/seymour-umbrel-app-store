# SBP-007 — Multi-Chain Provider Catalog Integration

Imports the frozen Seymour Blockchain Runtime Version 1.0 provider catalog
into the Seymour Umbrel app-store repository.

## Adds

- nine-chain provider catalog;
- catalog loader and validator;
- Umbrel provider-list API contract;
- install-selection guardrails;
- BCH marked as the only live selectable provider;
- all other providers marked planned;
- architecture, ports, disk estimate, image, and availability metadata;
- status-page JSON output;
- compatibility tests preserving the existing BCH app;
- no live app update and no image publication.

## Run

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```
