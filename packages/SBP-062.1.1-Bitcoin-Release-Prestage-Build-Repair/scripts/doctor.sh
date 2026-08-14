#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-062.1.1 doctor: checking Bitcoin release prestage prerequisites"

test -f "$ROOT/runtime-images/bitcoin-core/Dockerfile"
test -f "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"

grep -q 'curl -fsSLO' \
  "$ROOT/runtime-images/bitcoin-core/Dockerfile"

echo "SBP-062.1.1 doctor: current network-build Dockerfile PASS"
echo "SBP-062.1.1 doctor: current workflow PASS"
echo "SBP-062.1.1 doctor: PASS"
