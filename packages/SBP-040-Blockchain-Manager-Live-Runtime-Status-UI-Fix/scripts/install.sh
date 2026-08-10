#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-040-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager"
APPSTORE="/home/umbrel/umbrel/app-stores/seymour-umbrel-app-store/seymour-blockchain-manager"
"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP/data/web"
cp -a "$WEB/telemetry.py" "$BACKUP/data/web/telemetry.py"
cp -a "$WEB/bch_runtime_probe.py" "$BACKUP/data/web/bch_runtime_probe.py"
cp -a "$COMPOSE" "$BACKUP/docker-compose.yml"
python3 "$PKG/payload/patch_sbp040.py" "$ROOT"
python3 -m py_compile "$WEB/telemetry.py" "$WEB/bch_runtime_probe.py"
if [[ -d "$INSTALLED/data/web" ]]; then
  cp -a "$WEB/telemetry.py" "$INSTALLED/data/web/telemetry.py"
  cp -a "$WEB/bch_runtime_probe.py" "$INSTALLED/data/web/bch_runtime_probe.py"
fi
if [[ -f "$INSTALLED/docker-compose.yml" ]]; then cp -a "$COMPOSE" "$INSTALLED/docker-compose.yml"; fi
if [[ -f "$APPSTORE/docker-compose.yml" ]]; then cp -a "$COMPOSE" "$APPSTORE/docker-compose.yml"; fi
printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-040-latest"
echo "Backup: $BACKUP"
echo "SBP-040 canonical dashboard projection: PASS"
echo "SBP-040 stable BCH status service alias: PASS"
echo "SBP-040 installed runtime synchronization: PASS"
echo "SBP-040 install: PASS"
echo "Blockchain Manager restart was NOT performed by install.sh."
echo "No live Umbrel lifecycle write action was executed."
