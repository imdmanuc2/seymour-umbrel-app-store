#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-026-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP/seymour-blockchain-manager/data/web"
cp \
  "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py" \
  "$BACKUP/seymour-blockchain-manager/data/web/nexus_integration.py"

cd "$ROOT"
python3 "$PKG/payload/patch_nexus_state_projection.py"

mkdir -p tests
cp "$PKG/payload/test_sbp026_projection_contract.py" tests/test_sbp026_projection_contract.py
cp "$PKG/payload/test_sbp026_runtime_state_values.py" tests/test_sbp026_runtime_state_values.py

echo "Backup: $BACKUP"
echo "SBP-026 install: PASS"
echo "No live Blockchain Manager restart was executed."
