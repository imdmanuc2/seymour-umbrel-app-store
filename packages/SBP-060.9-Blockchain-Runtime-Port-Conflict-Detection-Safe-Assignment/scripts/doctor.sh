#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-060.9 doctor: checking runtime port conflict prerequisites"
test -f "$ROOT/shared/blockchain_recovery/engine.py"
test -f "$ROOT/shared/blockchain_recovery/models.py"
test -f "$ROOT/scripts/seymour-blockchain-heal"
test -f "$ROOT/seymour-bitcoin-node/docker-compose.yml"
echo "SBP-060.9 doctor: recovery engine PASS"
echo "SBP-060.9 doctor: recovery CLI PASS"
echo "SBP-060.9 doctor: Bitcoin runtime definition PASS"
echo "SBP-060.9 doctor: PASS"
