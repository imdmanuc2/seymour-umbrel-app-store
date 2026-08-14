#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-062.1.1 doctor: checking direct Buildx publish prerequisites"
test -f "$ROOT/runtime-images/bitcoin-core/Dockerfile"
test -f "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"
echo "SBP-062.1.1 doctor: Bitcoin build context PASS"
echo "SBP-062.1.1 doctor: existing workflow PASS"
echo "SBP-062.1.1 doctor: PASS"
