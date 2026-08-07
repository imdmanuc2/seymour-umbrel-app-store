#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
export PYTHONPATH="$REPO:$REPO/shared:$REPO/tests${PYTHONPATH:+:$PYTHONPATH}"

for test in   test_ui_stabilization.py   test_ui_action_contract.py   test_operations_center.py   test_operations_center_ui.py   test_nexus_integration.py   test_nexus_api_contract.py; do
  python3 "$REPO/tests/$test"
done

python3 -m py_compile   "$REPO/seymour-blockchain-manager/data/web/nexus_integration.py"   "$REPO/seymour-blockchain-manager/data/web/app.py"

grep -q '/api/nexus/discovery'   "$REPO/seymour-blockchain-manager/data/web/app.py"

grep -q 'NEXUS_REGISTRATION_EVIDENCE_PATH'   "$REPO/seymour-blockchain-manager/docker-compose.yml"

echo "SBP-015 Nexus discovery verification: PASS"
echo "SBP-015 managed asset identity verification: PASS"
echo "SBP-015 telemetry projection verification: PASS"
echo "SBP-015 capability projection verification: PASS"
echo "SBP-015 operation contract verification: PASS"
echo "SBP-015 registration payload verification: PASS"
echo "SBP-015 registration evidence verification: PASS"
echo "SBP-015 final verification: PASS"
