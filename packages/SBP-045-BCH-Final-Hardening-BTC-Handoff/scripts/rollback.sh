#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-045-latest"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

[[ -f "$MARKER" ]] || {
  echo "SBP-045 rollback: backup marker missing"
  exit 1
}
BACKUP="$(cat "$MARKER")"

cp -a "$BACKUP/app.js" "$WEB/app.js"
cp -a "$BACKUP/operations_center.py" "$WEB/operations_center.py"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
  cp -a "$WEB/operations_center.py" "$INSTALLED/operations_center.py"
fi

echo "SBP-045 rollback: BCH final hardening files restored"
echo "Blockchain Manager restart is required after rollback."
echo "SBP-045 rollback: PASS"
