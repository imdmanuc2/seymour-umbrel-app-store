#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-062 doctor: checking Bitcoin multi-arch image prerequisites"

test -f "$ROOT/seymour-bitcoin-node/docker-compose.yml"
test -f "$ROOT/shared/runtime_architecture.py"

grep -q \
  'ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0' \
  "$ROOT/seymour-bitcoin-node/docker-compose.yml"

echo "SBP-062 doctor: Bitcoin runtime definition PASS"
echo "SBP-062 doctor: architecture guard dependency PASS"
echo "SBP-062 doctor: canonical image identity PASS"
echo "SBP-062 doctor: PASS"
