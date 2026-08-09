#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

python3 "$ROOT/tests/test_sbp023_runtime_probe.py"
python3 "$ROOT/tests/test_sbp023_lifecycle_contract.py"
python3 "$ROOT/tests/test_sbp023_native_client_contract.py"
python3 -m py_compile   "$ROOT/shared/umbrel_control/bridge.py"   "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"

echo "SBP-023 native lifecycle semantics verification: PASS"
echo "SBP-023 lifecycle error reporting verification: PASS"
echo "SBP-023 BCH sidecar observation verification: PASS"
echo "SBP-023 final verification: PASS"
