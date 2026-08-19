# SBP-068 — Multi-Family Provider Runtime Foundation

Purpose: remove Bitcoin-family assumptions from the provider/runtime
contract before introducing the first CryptoNote managed runtime.

This package does not install or activate Monero.

Objectives:

- allow multiple live/selectable providers in the provider catalog;
- remove the obsolete SBP-007 Bitcoin Cash-only catalog invariant;
- introduce provider runtime metadata;
- describe provider-specific RPC authentication requirements;
- establish Monero runtime identity without making Monero selectable;
- preserve Bitcoin and Bitcoin Cash provider behavior;
- verify generic managed-runtime and storage contracts remain provider-neutral.

Monero remains planned and non-selectable after this package.

No blockchain runtime is stopped, started, restarted, recreated,
updated, installed, or uninstalled.
