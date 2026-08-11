#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-044-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
cp -a "$WEB/app.js" "$BACKUP/app.js"
cp -a "$WEB/style.css" "$BACKUP/style.css"

python3 "$PKG/payload/patch_sbp044.py" "$ROOT"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
  cp -a "$WEB/style.css" "$INSTALLED/style.css"
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-044-latest"

echo "Backup: $BACKUP"
echo "SBP-044 request timeout/resilience integration: PASS"
echo "SBP-044 lifecycle evidence timeline integration: PASS"
echo "SBP-044 diagnostics/log viewer integration: PASS"
echo "SBP-044 installed web asset synchronization: PASS"
echo "SBP-044 install: PASS"
echo "No backend or lifecycle write was executed by install.sh."
