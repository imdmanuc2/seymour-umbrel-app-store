#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -f "$BACKUP/app.js" ]] || {
  echo "Invalid SBP-014A backup: $BACKUP" >&2
  exit 1
}

cp "$BACKUP/app.js" \
  "$REPO/seymour-blockchain-manager/data/web/app.js"

rm -f \
  "$REPO/tests/test_ui_stabilization.py" \
  "$REPO/tests/test_ui_action_contract.py"

echo "SBP-014A rollback: PASS"
