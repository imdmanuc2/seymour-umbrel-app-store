# SBP-021 — BCH RPC Health Repair & Status Contract

Target: /home/umbrel/seymour-umbrel-app-store-git (master)

Adds direct BCH JSON-RPC diagnostics, structured auth/transport errors, chain metrics,
and a `/api/runtime/bch-rpc` endpoint. It preserves installed/running runtime truth
while RPC is degraded. No live container is restarted automatically.
