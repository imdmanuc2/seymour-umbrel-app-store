#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-041-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
cp -a "$WEB/app.js" "$BACKUP/app.js"
cp -a "$WEB/style.css" "$BACKUP/style.css"

python3 "$PKG/payload/patch_sbp041.py" "$ROOT"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
  cp -a "$WEB/style.css" "$INSTALLED/style.css"
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-041-latest"

echo "Backup: $BACKUP"
echo "SBP-041 runtime presentation stabilization: PASS"
echo "SBP-041 sync presentation enhancement: PASS"
echo "SBP-041 installed web asset synchronization: PASS"
echo "SBP-041 install: PASS"
echo "No lifecycle write was executed."
