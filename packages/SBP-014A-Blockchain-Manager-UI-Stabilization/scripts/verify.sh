#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$REPO:$REPO/shared:$REPO/tests${PYTHONPATH:+:$PYTHONPATH}"

python3 "$REPO/tests/test_ui_stabilization.py"
python3 "$REPO/tests/test_ui_action_contract.py"
python3 "$REPO/tests/test_operations_center.py"
python3 "$REPO/tests/test_operations_center_ui.py"

echo "SBP-014A renderFilters repair verification: PASS"
echo "SBP-014A provider action bar verification: PASS"
echo "SBP-014A event binding deduplication verification: PASS"
echo "SBP-014A operations center restoration verification: PASS"
echo "SBP-014A final verification: PASS"
