#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
cd "$ROOT"

python3 tests/test_sbp030_lifecycle_model.py
python3 tests/test_sbp030_contract.py

python3 -m py_compile   shared/app_lifecycle/model.py   shared/app_lifecycle/engine.py   scripts/seymour-app-lifecycle

echo
echo "===== SAMPLE RESTART PLAN ====="
python3 scripts/seymour-app-lifecycle   seymour-bch-node   restart   --state ready   --installed   --running   --healthy true

echo
echo "SBP-030 lifecycle planner verification: PASS"
echo "SBP-030 native lifecycle safety contract verification: PASS"
echo "SBP-030 final verification: PASS"
