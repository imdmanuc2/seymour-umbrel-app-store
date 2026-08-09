#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-025-$STAMP"
"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP/seymour-blockchain-manager/data/web"
cp "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$BACKUP/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
cp "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py" "$BACKUP/seymour-blockchain-manager/data/web/nexus_integration.py"
cd "$ROOT"
cp "$PKG/payload/runtime_state.py" seymour-blockchain-manager/data/web/runtime_state.py
python3 "$PKG/payload/patch_runtime_probe.py"
python3 "$PKG/payload/patch_nexus_integration.py"
mkdir -p tests
cp "$PKG/payload/tests/test_sbp025_runtime_state.py" tests/test_sbp025_runtime_state.py
cp "$PKG/payload/tests/test_sbp025_runtime_contract.py" tests/test_sbp025_runtime_contract.py
echo "Backup: $BACKUP"
echo "SBP-025 install: PASS"
echo "No live Blockchain Manager restart was executed."
