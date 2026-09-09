# SBP-077.1 — Shared Blockchain Target Runtime Installer

Provides the guarded target-local installer for an already-built and
verified SBP-077 runtime artifact.

Production target:

    /home/umbrel/umbrel/seymour-runtime

The installer:

- takes an existing runtime artifact directory
- verifies its required runtime contract before promotion
- calculates a deterministic payload manifest
- serializes deployment with an exclusive file lock
- stages the artifact on the target filesystem
- preserves at most one previous runtime
- promotes using directory rename operations
- verifies the promoted runtime
- rolls back automatically if promoted verification fails
- supports an explicit rollback operation
- writes durable current and historical evidence

It does not:

- install a blockchain
- materialize storage
- perform Docker lifecycle
- execute arbitrary shell/command/argv
- depend on Nexus Command Center
- depend on Seymour Blockchain Manager

Production paths are owned by the installer. Tests inject an alternate
Umbrel root through the Python API; the public CLI does not expose a
target-root option.
