#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-016-$STAMP"

"$ROOT/scripts/doctor.sh" "$REPO"

mkdir -p "$BACKUP"

cp -a \
  "$REPO/seymour-blockchain-manager" \
  "$BACKUP/"

cp \
  "$ROOT/payload/nexus_delivery.py" \
  "$REPO/seymour-blockchain-manager/data/web/nexus_delivery.py"

cd "$REPO"

python3 "$ROOT/payload/patch_app.py"
python3 "$ROOT/payload/patch_compose.py"

mkdir -p "$REPO/tests"

cp \
  "$ROOT/payload/test_nexus_delivery.py" \
  "$REPO/tests/test_nexus_delivery.py"

cp \
  "$ROOT/payload/test_nexus_delivery_retry.py" \
  "$REPO/tests/test_nexus_delivery_retry.py"

cp \
  "$ROOT/payload/test_nexus_delivery_api.py" \
  "$REPO/tests/test_nexus_delivery_api.py"

echo "Backup: $BACKUP"
echo "SBP-016 install: PASS"
echo "No Nexus delivery was executed."
echo "No live Umbrel app was restarted."
