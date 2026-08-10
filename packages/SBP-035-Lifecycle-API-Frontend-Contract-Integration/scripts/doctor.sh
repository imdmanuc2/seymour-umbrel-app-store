#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
for rel in \
  shared/app_lifecycle/engine.py \
  shared/app_lifecycle/executor.py \
  shared/app_lifecycle/projection.py \
  shared/app_lifecycle/audit.py \
  shared/app_lifecycle/operations.py \
  shared/contracts/app-lifecycle-operation-v1.json; do
  [[ -f "$ROOT/$rel" ]] || { echo "SBP-035 doctor: missing required $rel" >&2; exit 1; }
done
python3 -m py_compile \
  "$ROOT/shared/app_lifecycle/engine.py" \
  "$ROOT/shared/app_lifecycle/executor.py" \
  "$ROOT/shared/app_lifecycle/projection.py" \
  "$ROOT/shared/app_lifecycle/audit.py" \
  "$ROOT/shared/app_lifecycle/operations.py"
echo "SBP-035 doctor: lifecycle Operations dependency chain compile PASS"
echo "SBP-035 doctor: PASS"
