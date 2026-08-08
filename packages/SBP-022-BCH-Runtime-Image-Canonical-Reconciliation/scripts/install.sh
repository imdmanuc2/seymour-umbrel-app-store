#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-022-$STAMP"
"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP/seymour-bch-node/data/node"
cp "$ROOT/seymour-bch-node/docker-compose.yml" "$BACKUP/seymour-bch-node/docker-compose.yml"
cp "$ROOT/seymour-bch-node/data/node/entrypoint.sh" "$BACKUP/seymour-bch-node/data/node/entrypoint.sh"
cd "$ROOT"
python3 "$PKG/payload/patch_bch_compose.py"
python3 "$PKG/payload/patch_healthcheck_source.py"
mkdir -p tests
cp "$PKG/payload/tests/test_bch_canonical_entrypoint.py" tests/test_bch_canonical_entrypoint.py
cp "$PKG/payload/tests/test_bch_recreation_contract.py" tests/test_bch_recreation_contract.py
cp "$PKG/payload/tests/test_bch_healthcheck_contract.py" tests/test_bch_healthcheck_contract.py
echo "Backup: $BACKUP"
echo "SBP-022 install: PASS"
echo "No live BCH container was recreated."
