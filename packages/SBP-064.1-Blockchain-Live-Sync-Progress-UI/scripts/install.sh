#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$ROOT/packages/SBP-064.1-Blockchain-Live-Sync-Progress-UI"
SOURCE="$ROOT/seymour-blockchain-manager/data/web/app.js"

INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/app.js"

"$PKG/scripts/doctor.sh"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-064.1-$STAMP"

mkdir -p "$BACKUP"
cp "$SOURCE" "$BACKUP/app.js"

python3 "$PKG/scripts/patch.py"

echo "SBP-064.1 repository source patch: PASS"

if [[ -f "$INSTALLED" ]]; then
  sudo cp "$SOURCE" "$INSTALLED"
  echo "SBP-064.1 installed Blockchain Manager source synchronized: PASS"
else
  echo "ERROR: installed Blockchain Manager app.js not found"
  exit 1
fi

echo "Backup: $BACKUP"
echo "SBP-064.1 install: PASS"
echo "No blockchain runtime was installed, stopped, started, restarted, recreated, or uninstalled."
echo "NEXT: run verify.sh, then restart Blockchain Manager only."
