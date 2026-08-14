#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

echo "SBP-060.10 doctor: checking Bitcoin architecture guard prerequisites"

test -f "$ROOT/shared/blockchain_recovery/models.py"
test -f "$ROOT/shared/blockchain_recovery/engine.py"
test -f "$ROOT/scripts/seymour-blockchain-heal"
test -f "$ROOT/scripts/seymour-bitcoin-managed-runtime"
test -f "$ROOT/seymour-bitcoin-node/docker-compose.yml"

grep -q 'seymour-bitcoin-node:29.0.0'   "$ROOT/seymour-bitcoin-node/docker-compose.yml"

echo "SBP-060.10 doctor: recovery model PASS"
echo "SBP-060.10 doctor: managed Bitcoin wrapper PASS"
echo "SBP-060.10 doctor: Bitcoin image reference PASS"
echo "SBP-060.10 doctor: PASS"
