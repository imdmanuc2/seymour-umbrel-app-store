#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$PKG/../.." && pwd)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-063.3.8-$TS"
MGR_LIVE="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"
BCH_LIVE="/home/umbrel/umbrel/app-data/seymour-bch-node/data/status"

"$PKG/scripts/doctor.sh"
mkdir -p "$BACKUP/repository" "$BACKUP/live-manager" "$BACKUP/live-bch"
cp -a "$REPO/seymour-blockchain-manager/data/web/app.js" "$BACKUP/repository/app.js"
cp -a "$REPO/seymour-blockchain-manager/data/web/telemetry.py" "$BACKUP/repository/telemetry.py"
cp -a "$REPO/seymour-bch-node/data/status/app.py" "$BACKUP/repository/bch-status-app.py"
[ -f "$MGR_LIVE/app.js" ] && cp -a "$MGR_LIVE/app.js" "$BACKUP/live-manager/app.js"
[ -f "$MGR_LIVE/telemetry.py" ] && cp -a "$MGR_LIVE/telemetry.py" "$BACKUP/live-manager/telemetry.py"
[ -f "$BCH_LIVE/app.py" ] && cp -a "$BCH_LIVE/app.py" "$BACKUP/live-bch/app.py"

python3 "$PKG/scripts/patch.py" \
  --app-js "$REPO/seymour-blockchain-manager/data/web/app.js" \
  --telemetry "$REPO/seymour-blockchain-manager/data/web/telemetry.py" \
  --status-app "$REPO/seymour-bch-node/data/status/app.py"
python3 -m py_compile \
  "$REPO/seymour-blockchain-manager/data/web/telemetry.py" \
  "$REPO/seymour-bch-node/data/status/app.py"
echo "SBP-063.3.8 repository source synchronized: PASS"

cp -a "$REPO/seymour-blockchain-manager/data/web/app.js" "$MGR_LIVE/app.js"
cp -a "$REPO/seymour-blockchain-manager/data/web/telemetry.py" "$MGR_LIVE/telemetry.py"
cp -a "$REPO/seymour-bch-node/data/status/app.py" "$BCH_LIVE/app.py"
echo "SBP-063.3.8 installed Manager/status source synchronized: PASS"

echo "Backup: $BACKUP"
echo "SBP-063.3.8 install: PASS"
echo "No blockchain node runtime was installed, stopped, restarted, recreated, or uninstalled."
echo "NEXT: run verify.sh; then restart Blockchain Manager and BCH status service only."
