# SBP-071 Acceptance

The GitHub workflow must complete:

1. `build-amd64`
2. `build-arm64`
3. `publish-manifest`

Required canonical image:

`ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1`

Required platforms:

- `linux/amd64`
- `linux/arm64`

The architecture builds must verify the official Monero 0.18.5.1 release SHA256
before building the image and must smoke-test `monerod --version`.

The provider catalog must remain:

- `availability: planned`
- `selectable: false`
- `productionImage: null`

until a later activation milestone.
