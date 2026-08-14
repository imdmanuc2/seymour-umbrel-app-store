# Bitcoin multi-architecture image publishing contract

Canonical image:
`ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0`

The tag must contain:
- linux/amd64
- linux/arm64

Recommended Buildx command in the actual image-build repository:

```bash
docker buildx create --use --name seymour-multiarch 2>/dev/null ||   docker buildx use seymour-multiarch

docker buildx inspect --bootstrap

docker buildx build   --platform linux/amd64,linux/arm64   --tag ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0   --push   .
```

Recommended GitHub Actions publishing steps:

```yaml
- uses: docker/setup-qemu-action@v3
- uses: docker/setup-buildx-action@v3
- uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

- uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    platforms: linux/amd64,linux/arm64
    tags: ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0
```

This package does not publish the missing ARM64 image. It makes incompatibility explicit
and fail-closed until the image-build repository is located and the manifest is published.
