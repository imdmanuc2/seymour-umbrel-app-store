#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

export PYTHONPATH="$REPO:$REPO/shared${PYTHONPATH:+:$PYTHONPATH}"

python3 "$REPO/tests/test_provider_catalog.py"
python3 "$REPO/tests/test_bch_catalog_compatibility.py"
python3 "$REPO/tests/test_blockchain_manager_ui.py"
python3 "$REPO/tests/test_blockchain_manager_catalog.py"
python3 "$REPO/tests/test_live_dashboard.py"
python3 "$REPO/tests/test_live_dashboard_contract.py"

python3 -m py_compile \
  "$REPO/seymour-blockchain-manager/data/web/telemetry.py" \
  "$REPO/seymour-blockchain-manager/data/web/app.py"

grep -q \
  '/api/dashboard' \
  "$REPO/seymour-blockchain-manager/data/web/app.py"

grep -q \
  '/var/run/docker.sock:/var/run/docker.sock:ro' \
  "$REPO/seymour-blockchain-manager/docker-compose.yml"

grep -q \
  'setInterval(refreshTelemetry, 5000)' \
  "$REPO/seymour-blockchain-manager/data/web/app.js"

echo "SBP-009 live dashboard verification: PASS"
echo "SBP-009 host telemetry verification: PASS"
echo "SBP-009 BCH telemetry verification: PASS"
echo "SBP-009 auto-refresh verification: PASS"
echo "SBP-009 final verification: PASS"
