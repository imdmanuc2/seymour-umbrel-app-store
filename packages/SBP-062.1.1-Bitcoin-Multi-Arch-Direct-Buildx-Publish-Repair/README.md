# SBP-062.1.1 — Bitcoin Multi-Arch Direct Buildx Publish Repair

Replaces docker/build-push-action with explicit docker buildx build --push commands for amd64 and arm64, then publishes the canonical manifest only after both architecture tags exist. No runtime restart or blockchain-data modification occurs during install.
