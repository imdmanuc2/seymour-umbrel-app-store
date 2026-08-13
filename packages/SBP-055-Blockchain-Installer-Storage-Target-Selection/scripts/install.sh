#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh" "$ROOT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-055-$STAMP"
mkdir -p "$BACKUP/seymour-blockchain-manager/data/web"
for f in installer.py app.py app.js; do
  cp -a "$ROOT/seymour-blockchain-manager/data/web/$f" "$BACKUP/seymour-blockchain-manager/data/web/$f"
done
cp "$PKG/payload/seymour-blockchain-manager/data/web/storage_targets.py" "$ROOT/seymour-blockchain-manager/data/web/storage_targets.py"
python3 "$PKG/scripts/patch.py" "$ROOT"
cp "$PKG/payload/tests/test_storage_target_selection.py" "$ROOT/tests/test_storage_target_selection.py"
printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-055-latest"
echo "Backup: $BACKUP"
echo "SBP-055 storage-target API installed: PASS"
echo "SBP-055 installer selection contract installed: PASS"
echo "SBP-055 wizard storage selector installed: PASS"
echo "SBP-055 install: PASS"
echo "No blockchain runtime was installed, restarted, moved, or reconfigured."
