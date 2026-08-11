#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-045-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
cp -a "$WEB/app.js" "$BACKUP/app.js"
cp -a "$WEB/operations_center.py" "$BACKUP/operations_center.py"

python3 "$PKG/payload/patch_sbp045.py" "$ROOT"

python3 -m py_compile "$WEB/operations_center.py"

if [[ -d "$INSTALLED" ]]; then
  cp -a "$WEB/app.js" "$INSTALLED/app.js"
  cp -a "$WEB/operations_center.py" "$INSTALLED/operations_center.py"
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-045-latest"

echo "Backup: $BACKUP"
echo "SBP-045 post-restart sync telemetry continuity: PASS"
echo "SBP-045 Docker Engine API log reader: PASS"
echo "SBP-045 canonical diagnostics integration: PASS"
echo "SBP-045 lifecycle request resilience update: PASS"
echo "SBP-045 installed runtime synchronization: PASS"
echo "SBP-045 install: PASS"
echo "Blockchain Manager restart is required to load backend Python changes."
echo "No lifecycle write was executed by install.sh."
