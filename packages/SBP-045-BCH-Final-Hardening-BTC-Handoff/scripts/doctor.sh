#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"

for f in "$WEB/app.js" "$WEB/operations_center.py" "$WEB/bch_runtime_probe.py"; do
  [[ -f "$f" ]] || { echo "SBP-045 doctor: missing $f"; exit 1; }
done

grep -Fq 'function presentedRuntime(provider)' "$WEB/app.js"
grep -Fq 'def diagnostics()' "$WEB/operations_center.py"
grep -Fq 'def recent_logs' "$WEB/operations_center.py"
grep -Fq 'DOCKER_SOCKET' "$WEB/bch_runtime_probe.py"

python3 -m py_compile \
  "$WEB/operations_center.py" \
  "$WEB/bch_runtime_probe.py"

echo "SBP-045 doctor: BCH final hardening anchors PASS"
echo "SBP-045 doctor: PASS"
