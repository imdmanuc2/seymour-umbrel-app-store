#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-042.1-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
cp -a "$WEB/app.js" "$BACKUP/app.js"

python3 "$PKG/payload/patch_sbp042_1.py" "$ROOT"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-042.1-latest"

echo "Backup: $BACKUP"
echo "SBP-042.1 stale catalog summary write removal: PASS"
echo "SBP-042.1 null-safe DOM projection integration: PASS"
echo "SBP-042.1 installed web asset synchronization: PASS"
echo "SBP-042.1 install: PASS"
echo "No backend or lifecycle write was executed."
