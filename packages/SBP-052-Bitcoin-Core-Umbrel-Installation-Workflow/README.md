# SBP-052 — Bitcoin Core Umbrel Installation Workflow

Adds a guarded Bitcoin Core installation wrapper that delegates to the existing
generic `scripts/seymour-umbrel-app` bridge.

This package does not install Bitcoin Core during doctor/install/verify.
A live install requires the exact confirmation token:

`INSTALL-seymour-bitcoin-node`
