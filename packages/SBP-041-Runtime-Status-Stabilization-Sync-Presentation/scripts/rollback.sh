#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-041-latest"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

[[ -f "$MARKER" ]] || {
  echo "SBP-041 rollback: backup marker missing"
  exit 1
}
BACKUP="$(cat "$MARKER")"

cp -a "$BACKUP/app.js" "$WEB/app.js"
cp -a "$BACKUP/style.css" "$WEB/style.css"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
  cp -a "$WEB/style.css" "$INSTALLED/style.css"
fi

echo "SBP-041 rollback: frontend runtime presentation restored"
echo "SBP-041 rollback: PASS"
