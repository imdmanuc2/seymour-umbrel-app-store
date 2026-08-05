# SBP-005 — Umbrel Application Control Bridge

Adds Seymour's guarded bridge to Umbrel's native authenticated TRPC app API.

## Commands

```bash
./scripts/seymour-umbrel-app list
./scripts/seymour-umbrel-app state seymour-bch-node
./scripts/seymour-umbrel-app logs seymour-bch-node

./scripts/seymour-umbrel-app install seymour-bch-node
./scripts/seymour-umbrel-app install seymour-bch-node \
  --execute \
  --confirm INSTALL-seymour-bch-node
```

Write commands remain plan-only unless both `--execute` and the exact confirmation
token are supplied.

## Supported lifecycle operations

- install
- uninstall
- start
- stop
- restart
- update
- state
- list
- logs

The bridge calls Umbrel's authenticated TRPC API. It does not run `docker compose`
or manipulate Umbrel app state files directly.
