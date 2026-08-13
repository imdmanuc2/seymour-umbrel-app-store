#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-060-latest"
[[ -f "$LATEST" ]] || { echo "SBP-060 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"

cp -a "$BACKUP/shared/provider_catalog/providers.v1.json" "$ROOT/shared/provider_catalog/providers.v1.json"
cp -a "$BACKUP/seymour-blockchain-manager/data/catalog/providers.v1.json" "$ROOT/seymour-blockchain-manager/data/catalog/providers.v1.json"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/app.py" "$ROOT/seymour-blockchain-manager/data/web/app.py"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/app.js" "$ROOT/seymour-blockchain-manager/data/web/app.js"
rm -f "$ROOT/tests/test_bitcoin_provider_activation.py"

echo "SBP-060 rollback: PASS"
echo "No running blockchain runtime or chain data was modified."
