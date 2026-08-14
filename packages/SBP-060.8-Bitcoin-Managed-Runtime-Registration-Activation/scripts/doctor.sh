#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-060.8 doctor: checking Bitcoin managed runtime prerequisites"

test -f "$ROOT/seymour-bitcoin-node/umbrel-app.yml"
test -f "$ROOT/scripts/seymour-umbrel-app"
test -f "$ROOT/shared/blockchain_install/runtime_binding.py"
test -f "$ROOT/shared/blockchain_install/start_guard.py"

grep -q 'bitcoin-mainnet' \
  "$ROOT/seymour-blockchain-manager/data/web/runtime_registry.py"

echo "SBP-060.8 doctor: Bitcoin app definition PASS"
echo "SBP-060.8 doctor: native Umbrel control bridge PASS"
echo "SBP-060.8 doctor: guarded storage dependencies PASS"
echo "SBP-060.8 doctor: provider-neutral runtime registry PASS"
echo "SBP-060.8 doctor: PASS"
