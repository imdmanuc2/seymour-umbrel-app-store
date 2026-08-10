#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
cd "$ROOT"
python3 tests/test_sbp030_lifecycle_model.py
python3 tests/test_sbp030_contract.py
python3 tests/test_sbp031_executor.py
python3 tests/test_sbp031_contract.py
python3 tests/test_sbp032_projection.py
python3 tests/test_sbp032_contract.py
python3 tests/test_sbp033_audit.py
python3 tests/test_sbp033_contract.py
python3 tests/test_sbp034_operations.py
python3 tests/test_sbp034_contract.py
python3 -m py_compile \
  shared/app_lifecycle/model.py \
  shared/app_lifecycle/engine.py \
  shared/app_lifecycle/executor.py \
  shared/app_lifecycle/projection.py \
  shared/app_lifecycle/audit.py \
  shared/app_lifecycle/operations.py
if grep -RniE 'docker[[:space:]]+(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' shared/app_lifecycle/operations.py; then
  echo "SBP-034 verify: direct Docker lifecycle command detected" >&2
  exit 1
fi
echo
echo "SBP-034 canonical Operations facade verification: PASS"
echo "SBP-034 planner/executor/projection/audit composition: PASS"
echo "SBP-034 duplicate execution path prohibition: PASS"
echo "SBP-034 direct Docker lifecycle prohibition: PASS"
echo "SBP-034 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
echo "verify.sh used a fake native bridge and temporary audit storage only."
