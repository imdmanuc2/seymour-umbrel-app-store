# SBP-071.1 — Monero Release Prestage Architecture Repair

Repairs the Monero multi-architecture GitHub Actions workflow after the arm64
prestage job attempted to execute an ARM64 `monerod` binary directly on the
x86_64 GitHub runner before QEMU was configured.

The official Monero 0.18.5.1 archive names and SHA256 values are unchanged.
Architecture execution remains covered later by Buildx/QEMU and the explicit
Docker `--platform` smoke test.

No blockchain runtime or provider activation state is modified.
