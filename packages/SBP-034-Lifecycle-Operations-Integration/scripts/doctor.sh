#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
[[ -d "$ROOT" ]] || { echo "SBP-034 doctor: repository missing: $ROOT" >&2; exit 1; }
for rel in \
  shared/app_lifecycle/engine.py \
  shared/app_lifecycle/executor.py \
  shared/app_lifecycle/projection.py \
  shared/app_lifecycle/audit.py \
  shared/umbrel_control/bridge.py; do
  [[ -f "$ROOT/$rel" ]] || { echo "SBP-034 doctor: required dependency missing: $rel" >&2; exit 1; }
done
python3 -m py_compile \
  "$ROOT/shared/app_lifecycle/engine.py" \
  "$ROOT/shared/app_lifecycle/executor.py" \
  "$ROOT/shared/app_lifecycle/projection.py" \
  "$ROOT/shared/app_lifecycle/audit.py"
echo "SBP-034 doctor: lifecycle dependency chain compile PASS"
echo "SBP-034 doctor: PASS"
