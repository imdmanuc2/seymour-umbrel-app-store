#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-023-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP/shared/umbrel_control" "$BACKUP/seymour-blockchain-manager/data/web"
cp "$ROOT/shared/umbrel_control/bridge.py" "$BACKUP/shared/umbrel_control/bridge.py"
cp "$ROOT/shared/umbrel_control/native-client.ts" "$BACKUP/shared/umbrel_control/native-client.ts"
cp "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$BACKUP/seymour-blockchain-manager/data/web/bch_runtime_probe.py"

cd "$ROOT"
python3 "$PKG/payload/patch_lifecycle_bridge.py"
python3 "$PKG/payload/patch_runtime_probe.py"

mkdir -p tests
cp "$PKG"/payload/tests/*.py tests/

echo "Backup: $BACKUP"
echo "SBP-023 install: PASS"
echo "No live Umbrel lifecycle action was executed."
