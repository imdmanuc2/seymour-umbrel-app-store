#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-055-latest"
[[ -f "$LATEST" ]] || { echo "SBP-055 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
for f in installer.py app.py app.js; do
  cp -a "$BACKUP/seymour-blockchain-manager/data/web/$f" "$ROOT/seymour-blockchain-manager/data/web/$f"
done
rm -f "$ROOT/seymour-blockchain-manager/data/web/storage_targets.py" "$ROOT/tests/test_storage_target_selection.py"
echo "SBP-055 rollback: PASS"
echo "No running blockchain runtime or chain data was modified."
