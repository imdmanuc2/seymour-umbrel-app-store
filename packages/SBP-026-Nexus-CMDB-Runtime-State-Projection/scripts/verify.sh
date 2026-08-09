#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

python3 "$ROOT/tests/test_sbp026_projection_contract.py"
python3 "$ROOT/tests/test_sbp026_runtime_state_values.py"

python3 -m py_compile \
  "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py" \
  "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py"

echo "SBP-026 Nexus CMDB projection verification: PASS"
echo "SBP-026 runtime current-state contract verification: PASS"
echo "SBP-026 final verification: PASS"
