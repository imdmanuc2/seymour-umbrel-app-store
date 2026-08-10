#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-037-latest"
[[ -f "$MARKER" ]] || { echo "SBP-037 rollback: backup marker missing"; exit 1; }
BACKUP="$(cat "$MARKER")"

for f in engine.py model.py executor.py __init__.py; do
  cp -a "$BACKUP/shared/app_lifecycle/$f" "$ROOT/shared/app_lifecycle/$f"
done
rm -f "$ROOT/shared/app_lifecycle/runtime_state.py"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/lifecycle_routes.py"   "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

echo "SBP-037 rollback: restored lifecycle engine/executor/routes"
echo "Blockchain Manager restart was NOT performed by rollback.sh."
echo "SBP-037 rollback: PASS"
