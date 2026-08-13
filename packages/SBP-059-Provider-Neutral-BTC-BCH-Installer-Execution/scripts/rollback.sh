#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-059-latest"
[[ -f "$LATEST" ]] || { echo "SBP-059 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/installer.py" "$ROOT/seymour-blockchain-manager/data/web/installer.py"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/app.js" "$ROOT/seymour-blockchain-manager/data/web/app.js"
rm -f "$ROOT/tests/test_provider_neutral_installer.py"
echo "SBP-059 rollback: PASS"
echo "No running blockchain runtime or chain data was modified."
