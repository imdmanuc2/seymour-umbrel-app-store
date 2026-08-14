# Acceptance

The workflow must show a successful release download/checksum step for both:
- x86_64 / linux/amd64
- aarch64 / linux/arm64

Then:
- `29.0-amd64` must exist
- `29.0-arm64` must exist
- canonical `29.0` must contain both linux/amd64 and linux/arm64

The Dockerfile must not perform network downloads.
