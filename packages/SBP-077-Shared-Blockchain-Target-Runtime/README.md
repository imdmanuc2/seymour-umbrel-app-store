# SBP-077 — Shared Blockchain Target Runtime

Builds a deterministic provider-neutral target runtime for guarded
blockchain installation.

Target installation root:

    /home/umbrel/umbrel/seymour-runtime

The runtime is shared infrastructure. It is not owned by Nexus Command
Center or Seymour Blockchain Manager.

This package does not install blockchain nodes and does not deploy the
runtime to a host.

## Generated artifact policy

`build/seymour-runtime` is generated output and is intentionally not
committed. `scripts/build.py` plus the allow-listed source components are
the authoritative package definition.

A target deployment must build or otherwise materialize this runtime from
a reviewed Seymour source revision before installation. Nexus must not
depend on a developer checkout or on Seymour Blockchain Manager.

Included architectural components:

- fixed blockchain installation entrypoint
- BTC/BCH/XMR provider controls
- Umbrel lifecycle bridge
- shared blockchain installation modules
- BCH installation workflow
- Umbrel runtime modules
- canonical provider catalog
- BTC/BCH/XMR Umbrel application definitions

Excluded:

- Nexus Command Center
- Seymour Blockchain Manager
- historical SBP package payloads
- tests
- Python bytecode/cache
- Git metadata
- arbitrary shell/command execution surfaces
