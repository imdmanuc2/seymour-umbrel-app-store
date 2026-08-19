# SBP-071.2 — Bitcoin IBD Healthcheck & Telemetry Timeout Resilience

Purpose: repair false-negative Bitcoin health during initial block download when
Bitcoin Core remains operational but RPC responses occasionally exceed aggressive
observer timeouts.

Observed condition:
- Docker node healthcheck exceeded its 10-second timeout repeatedly;
- the Bitcoin node continued advancing block height;
- direct `bitcoin-cli uptime` and `getblockchaininfo` succeeded;
- the status service retained valid cached Bitcoin telemetry but marked RPC degraded
  after short reachability timeouts.

This package:
- raises the Bitcoin Docker healthcheck timeout from 10s to 30s;
- raises the lightweight status reachability timeout to a configurable 30s default;
- preserves the existing heavy-RPC timeout and stale-cache behavior;
- does not change blockchain data, storage bindings, RPC identity, or sync behavior.

The package source/install phase does not restart Bitcoin. A Bitcoin-only native
restart is required afterward to activate the Docker Compose healthcheck change.
Bitcoin Cash must remain untouched.
