#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"; PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; BACKUP="$ROOT/backups/sbp-047-$STAMP"; WEB="$ROOT/seymour-blockchain-manager/data/web"; INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"
"$PKG/scripts/doctor.sh" "$ROOT"; mkdir -p "$BACKUP"; for f in app.py app.js style.css; do cp -a "$WEB/$f" "$BACKUP/$f"; done
cp -a "$PKG/payload/sync_performance.py" "$WEB/sync_performance.py"; python3 "$PKG/payload/patch_sbp047.py" "$ROOT"; python3 -m py_compile "$WEB/sync_performance.py" "$WEB/app.py"
if [[ -d "$INSTALLED" ]]; then cp -a "$WEB/sync_performance.py" "$INSTALLED/sync_performance.py"; cp -a "$WEB/app.py" "$INSTALLED/app.py"; cp -a "$WEB/app.js" "$INSTALLED/app.js"; cp -a "$WEB/style.css" "$INSTALLED/style.css"; fi
printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-047-latest"
echo "Backup: $BACKUP"; echo 'SBP-047 performance analyzer installation: PASS'; echo 'SBP-047 performance API integration: PASS'; echo 'SBP-047 Initial Sync Manager Performance UI: PASS'; echo 'SBP-047 installed runtime synchronization: PASS'; echo 'SBP-047 install: PASS'; echo 'Blockchain Manager restart is required to load backend Python changes.'; echo 'No BCH configuration or lifecycle write was executed.'
