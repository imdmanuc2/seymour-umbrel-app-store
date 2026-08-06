# SBP-008 — Seymour Blockchain Manager UI Foundation

Adds the first catalog-driven Umbrel-facing blockchain manager page.

## Adds

- multi-chain catalog UI;
- provider cards for all nine Version 1.0 providers;
- BCH marked available;
- planned providers marked coming soon;
- architecture, ports, implementation, algorithm, and disk metadata;
- catalog API endpoint;
- provider-detail endpoint;
- BCH install-action contract;
- responsive static HTML/CSS/JavaScript;
- compatibility tests preserving the live BCH app.

## Run

```bash
chmod +x scripts/*.sh
./scripts/doctor.sh
./scripts/install.sh
./scripts/verify.sh
```

No live app is restarted, no image is published, and no blockchain is installed.
