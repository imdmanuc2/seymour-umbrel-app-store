#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
cd "$ROOT"

python3 tests/test_sbp030_lifecycle_model.py
python3 tests/test_sbp030_contract.py
python3 tests/test_sbp031_executor.py
python3 tests/test_sbp031_contract.py

python3 -m py_compile \
  shared/app_lifecycle/model.py \
  shared/app_lifecycle/engine.py \
  shared/app_lifecycle/executor.py \
  scripts/seymour-app-lifecycle

echo
echo "===== SAFE PLANNER REGRESSION ====="
python3 scripts/seymour-app-lifecycle \
  seymour-bch-node \
  restart \
  --state running \
  --installed \
  --running \
  --healthy true

echo
echo "SBP-031 planner regression verification: PASS"
echo "SBP-031 fake native execution verification: PASS"
echo "SBP-031 direct Docker lifecycle prohibition: PASS"
echo "SBP-031 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
