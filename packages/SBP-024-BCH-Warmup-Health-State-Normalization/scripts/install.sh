#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-024-$STAMP"
"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP/seymour-bch-node/data/status" "$BACKUP/shared/umbrel_control"
cp "$ROOT/seymour-bch-node/docker-compose.yml" "$BACKUP/seymour-bch-node/docker-compose.yml"
cp "$ROOT/seymour-bch-node/data/status/app.py" "$BACKUP/seymour-bch-node/data/status/app.py"
cp "$ROOT/shared/umbrel_control/bridge.py" "$BACKUP/shared/umbrel_control/bridge.py"
cd "$ROOT"
python3 "$PKG/payload/patch_bch_healthcheck.py"
python3 "$PKG/payload/patch_lifecycle_reconciliation.py"
mkdir -p tests
cp "$PKG"/payload/tests/*.py tests/
echo "Backup: $BACKUP"
echo "SBP-024 install: PASS"
echo "No live BCH restart was executed."
