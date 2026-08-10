#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

for f in \
  "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py" \
  "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" \
  "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py" \
  "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py" \
  "$ROOT/shared/app_lifecycle/runtime_state.py"
do
  [[ -f "$f" ]] || { echo "SBP-038 doctor: missing $f"; exit 1; }
done

grep -Fq 'operationalState' "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
grep -Fq 'runtimeState' "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"
grep -Fq 'CanonicalRuntimeStateProvider' "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

echo "SBP-038 doctor: runtime-state consumer anchors PASS"
echo "SBP-038 doctor: PASS"
