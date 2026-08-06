#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$REPO:$REPO/shared:$REPO/tests${PYTHONPATH:+:$PYTHONPATH}"
for test in test_provider_catalog.py test_bch_catalog_compatibility.py test_blockchain_manager_ui.py test_blockchain_manager_catalog.py test_live_dashboard.py test_live_dashboard_contract.py test_guarded_lifecycle.py test_lifecycle_ui_contract.py test_installation_wizard.py test_installation_wizard_ui.py; do python3 "$REPO/tests/$test"; done
python3 -m py_compile "$REPO/seymour-blockchain-manager/data/web/installer.py" "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q "/api/install/execute" "$REPO/seymour-blockchain-manager/data/web/app.py"
grep -q 'CONFIRMATION_TOKEN = f"INSTALL-{BCH_APP_ID}"' \
  "$REPO/seymour-blockchain-manager/data/web/installer.py"
grep -q "openInstallWizard" "$REPO/seymour-blockchain-manager/data/web/app.js"
echo "SBP-011 installation preflight verification: PASS"
echo "SBP-011 generated credential verification: PASS"
echo "SBP-011 guarded install confirmation verification: PASS"
echo "SBP-011 installation evidence verification: PASS"
echo "SBP-011 post-install verification: PASS"
echo "SBP-011 installation wizard UI verification: PASS"
echo "SBP-011 final verification: PASS"
