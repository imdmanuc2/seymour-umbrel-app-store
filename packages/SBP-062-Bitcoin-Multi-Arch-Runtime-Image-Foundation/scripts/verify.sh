#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
DOCKERFILE="$ROOT/runtime-images/bitcoin-core/Dockerfile"
WORKFLOW="$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"

echo "SBP-062 verify: Bitcoin multi-arch runtime image foundation"

test -f "$DOCKERFILE"
test -f "$WORKFLOW"

grep -q 'amd64) release_arch="x86_64"' "$DOCKERFILE"
grep -q 'arm64) release_arch="aarch64"' "$DOCKERFILE"
grep -q 'SHA256SUMS' "$DOCKERFILE"
grep -q 'sha256sum -c' "$DOCKERFILE"
grep -q 'linux/amd64,linux/arm64' "$WORKFLOW"
grep -q 'ghcr.io/imdmanuc2/seymour-bitcoin-node' "$WORKFLOW"
grep -q 'BITCOIN_VERSION: "29.0"' "$WORKFLOW"

echo "SBP-062 architecture mapping contract: PASS"
echo "SBP-062 release checksum contract: PASS"
echo "SBP-062 multi-arch publishing contract: PASS"
echo "SBP-062 final verification: PASS"
echo "No image was published and no live runtime was modified."
