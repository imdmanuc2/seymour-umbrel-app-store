#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"; PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; BACKUP="$ROOT/backups/sbp-020-$STAMP"
"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP" "$ROOT/tests"
cp "$ROOT/seymour-blockchain-manager/data/web/app.py" "$BACKUP/app.py"
cp "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py" "$BACKUP/nexus_integration.py"
cp "$PKG/payload/bch_runtime_probe.py" "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
cp "$PKG/payload/tests/test_bch_runtime_probe.py" "$ROOT/tests/test_bch_runtime_probe.py"
cp "$PKG/payload/tests/test_bch_runtime_contract.py" "$ROOT/tests/test_bch_runtime_contract.py"
cd "$ROOT"; python3 "$PKG/payload/patch_nexus_integration.py"; python3 "$PKG/payload/patch_app.py"
echo "Backup: $BACKUP"; echo "SBP-020 install: PASS"; echo "No live container was restarted."
