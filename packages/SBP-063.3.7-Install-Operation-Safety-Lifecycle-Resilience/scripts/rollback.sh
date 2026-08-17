#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "$0")/.." && pwd)"
REPO="$(cd "$PKG/../.." && pwd)"
BACKUP="${1:-$(find "$REPO/backups" -maxdepth 1 -type d -name 'sbp-063.3.7-*' | sort | tail -1)}"
[ -n "$BACKUP" ] && [ -d "$BACKUP" ] || { echo "ERROR: backup not found"; exit 1; }
LIVE="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data"
for f in web/app.js web/installer.py shared/umbrel_control/bridge.py shared/umbrel_control/http_client.py; do
  [ -f "$BACKUP/repository/$f" ] && cp -a "$BACKUP/repository/$f" "$REPO/seymour-blockchain-manager/data/$f"
  [ -f "$BACKUP/live/$f" ] && cp -a "$BACKUP/live/$f" "$LIVE/$f"
done
echo "SBP-063.3.7 rollback: PASS"
echo "Restart Blockchain Manager only to load rolled-back source."
