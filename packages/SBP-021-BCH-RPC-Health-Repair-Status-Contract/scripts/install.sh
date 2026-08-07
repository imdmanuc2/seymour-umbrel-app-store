#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"; BACKUP="$ROOT/backups/sbp-021-$STAMP"
"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP/seymour-blockchain-manager/data/web"
cp "$ROOT/seymour-blockchain-manager/data/web/app.py" "$BACKUP/seymour-blockchain-manager/data/web/app.py"
cp "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$BACKUP/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
cp "$ROOT/seymour-blockchain-manager/docker-compose.yml" "$BACKUP/seymour-blockchain-manager/docker-compose.yml"
cd "$ROOT"
cp "$PKG/payload/bch_rpc_probe.py" seymour-blockchain-manager/data/web/bch_rpc_probe.py
python3 "$PKG/payload/patch_runtime_probe.py"
python3 "$PKG/payload/patch_app.py"
python3 "$PKG/payload/patch_compose.py"
mkdir -p tests
cp "$PKG/payload/tests/test_bch_rpc_probe.py" tests/test_bch_rpc_probe.py
cp "$PKG/payload/tests/test_bch_rpc_contract.py" tests/test_bch_rpc_contract.py
echo "Backup: $BACKUP"
echo "SBP-021 install: PASS"
echo "No live container was restarted."
