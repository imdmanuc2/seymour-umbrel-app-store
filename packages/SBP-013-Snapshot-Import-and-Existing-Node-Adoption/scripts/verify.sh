#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$REPO:$REPO/shared:$REPO/tests${PYTHONPATH:+:$PYTHONPATH}"
for test in test_provider_catalog.py test_bch_catalog_compatibility.py test_blockchain_manager_ui.py test_blockchain_manager_catalog.py test_live_dashboard.py test_live_dashboard_contract.py test_guarded_lifecycle.py test_lifecycle_ui_contract.py test_installation_wizard.py test_installation_wizard_ui.py test_sync_manager.py test_sync_manager_ui.py test_adoption.py test_adoption_ui.py; do
  python3 "$REPO/tests/$test"
done
python3 -m py_compile "$REPO/seymour-blockchain-manager/data/web/adoption.py" "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q '/api/adoption/execute' "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q 'ADOPTION_EVIDENCE_PATH' "$REPO/seymour-blockchain-manager/docker-compose.yml"
echo "SBP-013 existing datadir detection verification: PASS"
echo "SBP-013 chain data validation verification: PASS"
echo "SBP-013 overwrite prevention verification: PASS"
echo "SBP-013 adoption planning verification: PASS"
echo "SBP-013 adoption confirmation verification: PASS"
echo "SBP-013 adoption evidence verification: PASS"
echo "SBP-013 post-adoption verification: PASS"
echo "SBP-013 final verification: PASS"
