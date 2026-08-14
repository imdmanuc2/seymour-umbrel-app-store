# Acceptance

Repository verification must prove:
- amd64 maps to x86_64 release binaries
- arm64 maps to aarch64 release binaries
- downloaded archive is checked against official SHA256SUMS
- GitHub Actions publishes linux/amd64 and linux/arm64
- canonical tag stays ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0

After the workflow publishes, live ARM64 acceptance is:

```bash
sudo docker pull ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0

sudo docker image inspect   ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0   --format 'Architecture={{.Architecture}}'

sudo docker run --rm   --entrypoint /bin/sh   ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0   -c 'uname -m; bitcoind --version | head -3'
```
