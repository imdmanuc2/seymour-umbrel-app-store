#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-038-latest"
[[ -f "$MARKER" ]] || { echo "SBP-038 rollback: backup marker missing"; exit 1; }
BACKUP="$(cat "$MARKER")"

cp -a "$BACKUP/web/runtime_state.py" \
  "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py"
cp -a "$BACKUP/web/lifecycle_routes.py" \
  "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"
cp -a "$BACKUP/app_lifecycle/runtime_state.py" \
  "$ROOT/shared/app_lifecycle/runtime_state.py"
rm -rf "$ROOT/shared/runtime_state"

echo "SBP-038 rollback: restored previous runtime-state consumers"
echo "Blockchain Manager restart was NOT performed by rollback.sh."
echo "SBP-038 rollback: PASS"
