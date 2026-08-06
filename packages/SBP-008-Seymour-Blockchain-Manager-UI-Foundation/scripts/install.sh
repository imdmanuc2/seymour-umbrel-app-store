#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-008-$STAMP"

"$ROOT/scripts/doctor.sh" "$REPO"

mkdir -p "$BACKUP"

if [[ -e "$REPO/seymour-blockchain-manager" ]]; then
  cp -a \
    "$REPO/seymour-blockchain-manager" \
    "$BACKUP/"
fi

mkdir -p "$REPO/tests"

cp -a \
  "$ROOT/payload/seymour-blockchain-manager" \
  "$REPO/seymour-blockchain-manager"

cp \
  "$REPO/shared/provider_catalog/providers.v1.json" \
  "$REPO/seymour-blockchain-manager/data/catalog/providers.v1.json"

cp \
  "$ROOT/payload/tests/test_blockchain_manager_ui.py" \
  "$REPO/tests/test_blockchain_manager_ui.py"

cp \
  "$ROOT/payload/tests/test_blockchain_manager_catalog.py" \
  "$REPO/tests/test_blockchain_manager_catalog.py"

echo "Backup: $BACKUP"
echo "SBP-008 install: PASS"
echo "No live Umbrel app was restarted."
echo "No container image was published."
