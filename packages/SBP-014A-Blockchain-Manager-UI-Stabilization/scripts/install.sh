#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-014a-$STAMP"

"$ROOT/scripts/doctor.sh" "$REPO"

mkdir -p "$BACKUP"
cp \
  "$REPO/seymour-blockchain-manager/data/web/app.js" \
  "$BACKUP/app.js"

cd "$REPO"
python3 "$ROOT/payload/repair_app_js.py"

mkdir -p "$REPO/tests"
cp "$ROOT/payload/tests/test_ui_stabilization.py" \
  "$REPO/tests/test_ui_stabilization.py"
cp "$ROOT/payload/tests/test_ui_action_contract.py" \
  "$REPO/tests/test_ui_action_contract.py"

echo "Backup: $BACKUP"
echo "SBP-014A install: PASS"
echo "No live Umbrel app was restarted."
echo "No blockchain operation was executed."
