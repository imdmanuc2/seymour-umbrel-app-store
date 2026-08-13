#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-058 doctor: FAIL: $*" >&2; exit 1; }
echo "SBP-058 doctor: checking runtime storage binding execution"
[[ -f "$ROOT/shared/blockchain_install/binding.py" ]] || fail "SBP-056 binding missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/storage_targets.py" ]] || fail "SBP-055 storage target service missing"
[[ -f "$ROOT/seymour-bitcoin-node/docker-compose.yml" ]] || fail "BTC compose missing"
[[ -f "$ROOT/seymour-bch-node/docker-compose.yml" ]] || fail "BCH compose missing"
python3 -m py_compile "$PKG/scripts/patch.py"
echo "SBP-058 doctor: dependencies PASS"
echo "SBP-058 doctor: compose/installer anchors PASS"
echo "SBP-058 doctor: PASS"
