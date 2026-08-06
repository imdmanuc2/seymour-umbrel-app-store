#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)";BACKUP="$REPO/backups/sbp-010-$STAMP"
"$ROOT/scripts/doctor.sh" "$REPO"
mkdir -p "$BACKUP";cp -a "$REPO/seymour-blockchain-manager" "$BACKUP/"
cp "$ROOT/payload/seymour-blockchain-manager/data/web/lifecycle.py" "$REPO/seymour-blockchain-manager/data/web/lifecycle.py"
(cd "$REPO" && python3 "$ROOT/payload/seymour-blockchain-manager/data/web/app.py.patch.py")
cat "$ROOT/payload/seymour-blockchain-manager/data/web/app.js.append" >> "$REPO/seymour-blockchain-manager/data/web/app.js"
(cd "$REPO" && python3 "$ROOT/payload/seymour-blockchain-manager/docker-compose.yml.patch.py")
mkdir -p "$REPO/tests";cp "$ROOT/payload/tests/test_guarded_lifecycle.py" "$REPO/tests/";cp "$ROOT/payload/tests/test_lifecycle_ui_contract.py" "$REPO/tests/"
echo "Backup: $BACKUP";echo 'SBP-010 install: PASS';echo 'No live Umbrel app was restarted.';echo 'No lifecycle command was executed.'
