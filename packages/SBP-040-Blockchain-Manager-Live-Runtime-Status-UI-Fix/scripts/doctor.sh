#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
for f in "$WEB/telemetry.py" "$WEB/bch_runtime_probe.py" "$WEB/bch_rpc_probe.py" "$WEB/app.js" "$ROOT/seymour-blockchain-manager/docker-compose.yml"; do
  [[ -f "$f" ]] || { echo "SBP-040 doctor: missing $f"; exit 1; }
done
grep -Fq 'def bch_telemetry()' "$WEB/telemetry.py"
grep -Fq 'def probe()' "$WEB/bch_runtime_probe.py"
grep -Fq 'operationalState' "$WEB/bch_runtime_probe.py"
grep -Fq 'telemetry?.runtimeState' "$WEB/app.js"
python3 -m py_compile "$WEB/telemetry.py" "$WEB/bch_runtime_probe.py" "$WEB/bch_rpc_probe.py"
echo "SBP-040 doctor: canonical dashboard/runtime anchors PASS"
echo "SBP-040 doctor: PASS"
