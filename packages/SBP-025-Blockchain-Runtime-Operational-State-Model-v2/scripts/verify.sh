#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

python3 \
  "$ROOT/tests/test_sbp025_runtime_state.py"

python3 \
  "$ROOT/tests/test_sbp025_runtime_contract.py"

python3 -m py_compile \
  "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py" \
  "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" \
  "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"

PYTHONPATH="$ROOT/seymour-blockchain-manager/data/web" \
python3 - <<'PY'
import runtime_state
assert "syncing" in runtime_state.VALID_RUNTIME_STATES
print("SBP-025 runtime module import verification: PASS")
PY

echo "SBP-025 runtime-state model verification: PASS"
echo "SBP-025 Nexus projection verification: PASS"
echo "SBP-025 final verification: PASS"
