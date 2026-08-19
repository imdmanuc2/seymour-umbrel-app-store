#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LATEST="$(find "$REPO/backups" -maxdepth 1 -type d -name 'sbp-069-*' | sort | tail -1)"
test -n "$LATEST" || { echo "ERROR: no SBP-069 backup found"; exit 1; }
SOURCE="$REPO/seymour-blockchain-manager/data/web/installer.py"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/installer.py"
cp "$LATEST/installer.py.repository" "$SOURCE"
if [[ -f "$LATEST/installer.py.installed" ]]; then
  sudo cp "$LATEST/installer.py.installed" "$INSTALLED"
fi
echo "SBP-069 rollback: PASS"
echo "No blockchain runtime was modified."
