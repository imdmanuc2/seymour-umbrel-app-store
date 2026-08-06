#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$REPO:$REPO/shared:$REPO/tests${PYTHONPATH:+:$PYTHONPATH}"
python3 "$REPO/tests/test_provider_catalog.py"
python3 "$REPO/tests/test_bch_catalog_compatibility.py"
python3 "$REPO/tests/test_blockchain_manager_ui.py"
python3 "$REPO/tests/test_blockchain_manager_catalog.py"
python3 "$REPO/tests/test_live_dashboard.py"
python3 "$REPO/tests/test_live_dashboard_contract.py"
python3 "$REPO/tests/test_guarded_lifecycle.py"
python3 "$REPO/tests/test_lifecycle_ui_contract.py"
python3 -m py_compile "$REPO/seymour-blockchain-manager/data/web/lifecycle.py" "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q '/api/lifecycle/' "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q 'LIFECYCLE_EVIDENCE_PATH' "$REPO/seymour-blockchain-manager/docker-compose.yml"
echo 'SBP-010 guarded lifecycle verification: PASS'
echo 'SBP-010 confirmation-token verification: PASS'
echo 'SBP-010 post-action verification: PASS'
echo 'SBP-010 lifecycle evidence verification: PASS'
echo 'SBP-010 UI lifecycle contract verification: PASS'
echo 'SBP-010 final verification: PASS'
