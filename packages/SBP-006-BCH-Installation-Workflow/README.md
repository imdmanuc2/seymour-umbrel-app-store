# SBP-006 — BCH Installation Workflow

Adds the first end-to-end guarded installation workflow for the Seymour Bitcoin
Cash Node Umbrel app.

## What it does

- verifies the BCH app source and version;
- verifies Umbrel and the native app-control bridge;
- checks available storage;
- captures the current Umbrel app state;
- creates an installation plan;
- optionally performs the Umbrel-native install;
- polls Umbrel installation state;
- inspects containers through the shared runtime bridge;
- probes the BCH status dashboard and health endpoint;
- writes structured operation evidence;
- creates a cleanup recommendation if installation fails.

## Safety

The workflow defaults to plan mode.

A live install requires:

```bash
./scripts/seymour-install-bch \
  --execute \
  --confirm INSTALL-seymour-bch-node
```

The workflow does not automatically uninstall the app on failure.
