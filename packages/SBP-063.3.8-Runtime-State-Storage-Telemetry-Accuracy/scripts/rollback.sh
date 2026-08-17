#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$PKG/../.." && pwd)"
BACKUP="${1:-}"
if [ -z "$BACKUP" ] || [ ! -d "$BACKUP" ]; then
  echo "Usage: $0 /path/to/backups/sbp-063.3.8-TIMESTAMP"
  exit 1
fi
cp -a "$BACKUP/repository/app.js" "$REPO/seymour-blockchain-manager/data/web/app.js"
cp -a "$BACKUP/repository/telemetry.py" "$REPO/seymour-blockchain-manager/data/web/telemetry.py"
cp -a "$BACKUP/repository/bch-status-app.py" "$REPO/seymour-bch-node/data/status/app.py"
[ -f "$BACKUP/live-manager/app.js" ] && cp -a "$BACKUP/live-manager/app.js" /home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/app.js
[ -f "$BACKUP/live-manager/telemetry.py" ] && cp -a "$BACKUP/live-manager/telemetry.py" /home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web/telemetry.py
[ -f "$BACKUP/live-bch/app.py" ] && cp -a "$BACKUP/live-bch/app.py" /home/umbrel/umbrel/app-data/seymour-bch-node/data/status/app.py
echo "SBP-063.3.8 rollback source restore: PASS"
echo "Restart Blockchain Manager and BCH status service only if the patched code had already been loaded."
