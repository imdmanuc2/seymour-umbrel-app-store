# SBP-077.2 — Shared Blockchain Target Runtime Bootstrap

Provides the guarded target-local bootstrap boundary for a previously
transferred and SHA-256-verified SBP-077 runtime bundle.

The bootstrap:

- accepts a target-local `seymour-runtime.tar.gz`
- validates the reviewed archive SHA-256 before extraction
- rejects path traversal, links, device nodes, FIFOs, sockets, and other
  unsupported archive members
- requires exactly one `seymour-runtime/` top-level tree
- extracts only into a target-owned temporary directory
- verifies the extracted payload manifest against the reviewed
  SBP-077.1-compatible payload manifest SHA-256
- invokes the existing SBP-077.1 directory installer
- removes temporary extraction state after completion

It does not:

- perform network transfer
- expose an extraction root or target runtime root on the public CLI
- accept arbitrary command/shell/argv
- install blockchain nodes itself
- materialize storage
- perform Docker lifecycle
- depend on Nexus Command Center
- depend on Seymour Blockchain Manager

The public CLI accepts only:

- `--archive`
- `--archive-sha256`
- `--payload-manifest-sha256`
- `--runtime-version`
- `--source-revision`

All production destination paths are owned internally by the bootstrap
and SBP-077.1.
