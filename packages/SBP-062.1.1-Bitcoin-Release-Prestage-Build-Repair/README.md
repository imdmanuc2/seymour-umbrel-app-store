# SBP-062.1.1 — Bitcoin Release Prestage Build Repair

Moves Bitcoin Core release download/checksum verification out of Docker BuildKit
and into an explicit GitHub Actions step.

The workflow:
- downloads the platform-specific Bitcoin Core archive on the GitHub runner
- downloads SHA256SUMS
- verifies the selected archive
- extracts bitcoind and bitcoin-cli into the build context
- builds a tiny architecture-specific runtime image from those verified binaries
- pushes amd64 and arm64 tags separately
- publishes the canonical manifest only after both tags exist

No image is published during package installation.
No blockchain runtime is restarted.
No blockchain data is modified.
