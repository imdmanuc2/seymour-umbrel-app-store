# SBP-060.7 — Runtime Start Storage Guard Integration

Wires storage-binding verification into the real Umbrel native start/restart path.

For Seymour blockchain apps with a `/data` bind:
- reject unresolved env-based bindings
- verify expected storage exists
- fail closed if `/mnt/...` falls back to `/`
- start/restart through native Umbrel control
- discover the `node` container via Compose labels
- verify live `/data` source matches persisted source
- if it does not, issue a protective native Umbrel stop and return failure

Docker is inspection-only; no direct Docker lifecycle is used.
The package installation itself does not restart a blockchain runtime.
