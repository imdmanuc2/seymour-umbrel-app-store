#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$REPO/seymour-blockchain-manager/data/web/installer.py"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/installer.py"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-069-$STAMP"

"$PKG/scripts/doctor.sh"
mkdir -p "$BACKUP"
cp "$SOURCE" "$BACKUP/installer.py.repository"
if sudo test -f "$INSTALLED"; then
  sudo cp "$INSTALLED" "$BACKUP/installer.py.installed"
fi

python3 "$PKG/scripts/patch.py" "$SOURCE"
python3 -m py_compile "$SOURCE"

if sudo test -f "$INSTALLED"; then
  sudo cp "$SOURCE" "$INSTALLED"
  sudo python3 -m py_compile "$INSTALLED"
fi

echo "SBP-069 install: PASS"
echo "Backup: $BACKUP"
echo "Monero remains non-selectable."
echo "No blockchain runtime was modified."
