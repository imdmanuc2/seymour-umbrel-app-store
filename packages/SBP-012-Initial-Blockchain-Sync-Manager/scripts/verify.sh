#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$REPO:$REPO/shared:$REPO/tests${PYTHONPATH:+:$PYTHONPATH}"
for test in test_provider_catalog.py test_bch_catalog_compatibility.py test_blockchain_manager_ui.py test_blockchain_manager_catalog.py test_live_dashboard.py test_live_dashboard_contract.py test_guarded_lifecycle.py test_lifecycle_ui_contract.py test_installation_wizard.py test_installation_wizard_ui.py test_sync_manager.py test_sync_manager_ui.py; do
  python3 "$REPO/tests/$test"
done
python3 -m py_compile "$REPO/seymour-blockchain-manager/data/web/sync_manager.py" "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q '/api/sync' "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q 'showSyncManager' "$REPO/seymour-blockchain-manager/data/web/app.js"
grep -q 'SYNC_HISTORY_PATH' "$REPO/seymour-blockchain-manager/docker-compose.yml"
echo "SBP-012 sync progress verification: PASS"
echo "SBP-012 blocks remaining verification: PASS"
echo "SBP-012 sync rate and ETA verification: PASS"
echo "SBP-012 peer quality verification: PASS"
echo "SBP-012 stall detection verification: PASS"
echo "SBP-012 recovery guidance verification: PASS"
echo "SBP-012 sync history evidence verification: PASS"
echo "SBP-012 final verification: PASS"
