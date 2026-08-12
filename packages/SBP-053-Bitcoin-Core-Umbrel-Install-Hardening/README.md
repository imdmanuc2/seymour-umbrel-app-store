# SBP-053 — Bitcoin Core Umbrel Install Hardening

Hardens the BTC Umbrel installation path discovered during the first live install.

Fixes:
- executable mode for the BTC node entrypoint
- executable mode for `scripts/seymour-install-btc`
- tracked `data/generated` and `data/state` directories
- installer rejects native `result: false`
- installer verifies final Umbrel app state before returning success

The package scripts do not restart or reinstall the running BTC node.
