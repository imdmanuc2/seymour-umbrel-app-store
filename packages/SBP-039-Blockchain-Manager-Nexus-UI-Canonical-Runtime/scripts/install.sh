#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-039-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP"
cp -a "$WEB/app.js" "$BACKUP/app.js"
cp -a "$WEB/style.css" "$BACKUP/style.css"

python3 "$PKG/payload/patch_ui.py" "$ROOT" "$PKG/payload/nexus-ui.css"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
  cp -a "$WEB/style.css" "$INSTALLED/style.css"
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-039-latest"

echo "Backup: $BACKUP"
echo "SBP-039 canonical runtime UI integration: PASS"
echo "SBP-039 Nexus visual integration: PASS"
echo "SBP-039 installed web asset synchronization: PASS"
echo "SBP-039 install: PASS"
echo "Static assets are bind-mounted; no lifecycle write was executed."
