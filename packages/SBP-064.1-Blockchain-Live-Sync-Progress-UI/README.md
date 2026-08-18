# SBP-064.1 — Blockchain Live Sync Progress UI

Improves the Blockchain Manager managed-runtime synchronization UI.

## Goals

- Preserve the existing 5-second `/api/dashboard` telemetry refresh.
- Show useful precision during very early blockchain synchronization.
- Make live block height and header target prominent.
- Display synchronization health guidance on the managed-runtime card.
- Keep peer count and chain-data footprint live.
- Automatically follow canonical runtime state as synchronization completes.
- Avoid introducing a second polling mechanism.
- Avoid modifying blockchain runtimes.

## Runtime safety

This package changes Blockchain Manager frontend presentation only.

It must not:

- stop a blockchain runtime;
- start a blockchain runtime;
- restart a blockchain runtime;
- recreate a blockchain runtime;
- modify blockchain data;
- alter storage bindings.
