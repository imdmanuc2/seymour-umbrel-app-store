#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"

for f in \
  "$ROOT/scripts/seymour-umbrel-app" \
  "$ROOT/seymour-bch-node/docker-compose.yml" \
  "$ROOT/seymour-blockchain-manager/docker-compose.yml" \
  "$WEB/app.py" \
  "$WEB/app.js" \
  "$WEB/telemetry.py" \
  "$WEB/bch_runtime_probe.py" \
  "$WEB/operations_center.py" \
  "$WEB/lifecycle_routes.py" \
  "$WEB/nexus_integration.py"
do
  [[ -f "$f" ]] || { echo "SBP-046 doctor: missing $f"; exit 1; }
done

grep -Fq 'operationalState' "$WEB/bch_runtime_probe.py"
grep -Fq 'runtimeState' "$WEB/telemetry.py"
grep -Fq '/api/lifecycle/operation' "$WEB/app.py"
grep -Fq 'def diagnostics()' "$WEB/operations_center.py"

echo "SBP-046 doctor: BCH acceptance anchors PASS"
echo "SBP-046 doctor: PASS"
