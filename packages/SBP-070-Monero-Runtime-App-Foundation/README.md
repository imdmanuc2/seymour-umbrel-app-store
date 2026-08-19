# SBP-070 — Monero Runtime App Foundation

Creates the canonical Seymour Umbrel app foundation for Monero without installing
or starting a Monero runtime.

Scope:
- `seymour-monero-node` Umbrel app manifest;
- portable Docker Compose runtime definition;
- provider-neutral data/RPC/status identity anchors;
- Monero `monerod` runtime command contract;
- status-service skeleton using Monero JSON-RPC semantics;
- pre-install identity materialization hook;
- non-selectable provider safety verification.

Monero remains planned/non-selectable after this package. The image reference is
canonical configuration only; this milestone does not require the image to exist
or be pulled.

No blockchain runtime is stopped, started, restarted, recreated, updated, installed,
or uninstalled.
