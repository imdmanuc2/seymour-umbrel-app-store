#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
echo "SBP-060.5 doctor: checking provider-neutral runtime projection prerequisites"
for f in app.js telemetry.py bch_runtime_probe.py; do test -f "$WEB/$f"; done
grep -q 'function installedProviders()' "$WEB/app.js"
grep -q 'const provider = live\[0\]' "$WEB/app.js"
grep -q '"bitcoin-cash-mainnet": bch_telemetry()' "$WEB/telemetry.py"
echo "SBP-060.5 doctor: current single-runtime anchors PASS"
echo "SBP-060.5 doctor: PASS"
