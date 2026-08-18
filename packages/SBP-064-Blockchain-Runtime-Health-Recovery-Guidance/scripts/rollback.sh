#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MARKER="$REPO/backups/sbp-064-last-backup"
test -f "$MARKER" || { echo "ERROR: no SBP-064 backup marker"; exit 1; }
BACKUP="$(cat "$MARKER")"
test -d "$BACKUP" || { echo "ERROR: backup missing: $BACKUP"; exit 1; }
cp -a "$BACKUP/seymour-blockchain-manager/data/web/telemetry.py" "$REPO/seymour-blockchain-manager/data/web/telemetry.py"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/app.js" "$REPO/seymour-blockchain-manager/data/web/app.js"
rm -f "$REPO/seymour-blockchain-manager/data/web/runtime_health.py"
LIVE="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data"
cp -a "$REPO/seymour-blockchain-manager/data/web/telemetry.py" "$LIVE/web/telemetry.py"
cp -a "$REPO/seymour-blockchain-manager/data/web/app.js" "$LIVE/web/app.js"
rm -f "$LIVE/web/runtime_health.py"
echo "SBP-064 rollback: PASS"
echo "Restart Blockchain Manager only to load rolled-back source."
