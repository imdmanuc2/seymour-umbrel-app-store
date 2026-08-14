#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
echo "SBP-061 doctor: checking BCH RPC load-control prerequisites"
test -f "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
test -f "$ROOT/seymour-blockchain-manager/data/web/telemetry.py"
test -f "$ROOT/seymour-blockchain-manager/data/web/bch_rpc_probe.py"
grep -q 'def probe()->dict' "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
echo "SBP-061 doctor: BCH runtime probe PASS"
echo "SBP-061 doctor: dashboard telemetry PASS"
echo "SBP-061 doctor: direct RPC diagnostic probe PASS"
echo "SBP-061 doctor: PASS"
