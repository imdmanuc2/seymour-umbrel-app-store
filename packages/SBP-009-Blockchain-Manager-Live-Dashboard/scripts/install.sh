#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-009-$STAMP"

"$ROOT/scripts/doctor.sh" "$REPO"

mkdir -p "$BACKUP"

cp -a \
  "$REPO/seymour-blockchain-manager" \
  "$BACKUP/"

cp \
  "$ROOT/payload/seymour-blockchain-manager/docker-compose.yml" \
  "$REPO/seymour-blockchain-manager/docker-compose.yml"

cp -a \
  "$ROOT/payload/seymour-blockchain-manager/data/web/." \
  "$REPO/seymour-blockchain-manager/data/web/"

mkdir -p "$REPO/tests"

cp \
  "$ROOT/payload/tests/test_live_dashboard.py" \
  "$REPO/tests/test_live_dashboard.py"

cp \
  "$ROOT/payload/tests/test_live_dashboard_contract.py" \
  "$REPO/tests/test_live_dashboard_contract.py"

cp \
  "$ROOT/payload/tests/test_blockchain_manager_ui.py" \
  "$REPO/tests/test_blockchain_manager_ui.py"

echo "Backup: $BACKUP"
echo "SBP-009 install: PASS"
echo "No live Umbrel app was restarted."
echo "No container image was published."
