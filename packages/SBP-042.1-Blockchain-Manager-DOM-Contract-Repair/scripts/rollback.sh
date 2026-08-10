#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-042.1-latest"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

[[ -f "$MARKER" ]] || {
  echo "SBP-042.1 rollback: backup marker missing"
  exit 1
}
BACKUP="$(cat "$MARKER")"

cp -a "$BACKUP/app.js" "$WEB/app.js"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
fi

echo "SBP-042.1 rollback: app.js restored"
echo "SBP-042.1 rollback: PASS"
