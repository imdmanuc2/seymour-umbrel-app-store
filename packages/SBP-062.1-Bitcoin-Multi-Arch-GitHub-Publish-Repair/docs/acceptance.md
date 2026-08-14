# Acceptance

The workflow must complete:
1. build-amd64
2. build-arm64
3. publish-manifest

The canonical tag must expose both linux/amd64 and linux/arm64.

After publishing, validate on .154 with docker pull, docker image inspect,
and an execution test showing Architecture=arm64 and uname -m=aarch64.
