#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
python3 "$ROOT/tests/test_sbp024_healthcheck_contract.py"
python3 "$ROOT/tests/test_sbp024_lifecycle_reconciliation.py"
python3 "$ROOT/tests/test_sbp024_status_contract.py"
python3 -m py_compile "$ROOT/shared/umbrel_control/bridge.py" "$ROOT/seymour-bch-node/data/status/app.py"
echo "SBP-024 Docker warmup normalization verification: PASS"
echo "SBP-024 native lifecycle reconciliation verification: PASS"
echo "SBP-024 status-state contract verification: PASS"
echo "SBP-024 final verification: PASS"
