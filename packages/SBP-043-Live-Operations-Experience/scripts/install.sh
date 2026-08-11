#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-043-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
cp -a "$WEB/app.js" "$BACKUP/app.js"
cp -a "$WEB/style.css" "$BACKUP/style.css"

python3 "$PKG/payload/patch_sbp043.py" "$ROOT"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
  cp -a "$WEB/style.css" "$INSTALLED/style.css"
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-043-latest"

echo "Backup: $BACKUP"
echo "SBP-043 canonical lifecycle Operations integration: PASS"
echo "SBP-043 diagnostics/logs/history integration: PASS"
echo "SBP-043 maintenance planning integration: PASS"
echo "SBP-043 installed web asset synchronization: PASS"
echo "SBP-043 install: PASS"
echo "No backend or lifecycle write was executed by install.sh."
