#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}";ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)";STAMP="$(date -u +%Y%m%dT%H%M%SZ)";BACKUP="$REPO/backups/sbp-014-$STAMP"
"$ROOT/scripts/doctor.sh" "$REPO";mkdir -p "$BACKUP";cp -a "$REPO/seymour-blockchain-manager" "$BACKUP/"
cp "$ROOT/payload/seymour-blockchain-manager/data/web/operations_center.py" "$REPO/seymour-blockchain-manager/data/web/operations_center.py"
cd "$REPO";python3 "$ROOT/payload/patch_app.py";python3 "$ROOT/payload/patch_compose.py";python3 "$ROOT/payload/patch_js.py"
grep -q 'function showOperationsCenter' "$REPO/seymour-blockchain-manager/data/web/app.js"||cat "$ROOT/payload/app.js.append" >> "$REPO/seymour-blockchain-manager/data/web/app.js"
grep -q '\.operations-actions' "$REPO/seymour-blockchain-manager/data/web/style.css"||cat "$ROOT/payload/style.css.append" >> "$REPO/seymour-blockchain-manager/data/web/style.css"
mkdir -p "$REPO/tests";cp "$ROOT/payload/tests/test_operations_center.py" "$REPO/tests/";cp "$ROOT/payload/tests/test_operations_center_ui.py" "$REPO/tests/"
echo "Backup: $BACKUP";echo "SBP-014 install: PASS";echo "No live backup, restore, upgrade, or restart was executed.";echo "No live Umbrel app was restarted."
