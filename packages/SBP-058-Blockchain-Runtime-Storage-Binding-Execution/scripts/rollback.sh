#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-058-latest"
[[ -f "$LATEST" ]] || { echo "SBP-058 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
cp -a "$BACKUP/seymour-bitcoin-node/docker-compose.yml" "$ROOT/seymour-bitcoin-node/docker-compose.yml"
cp -a "$BACKUP/seymour-bch-node/docker-compose.yml" "$ROOT/seymour-bch-node/docker-compose.yml"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/installer.py" "$ROOT/seymour-blockchain-manager/data/web/installer.py"
rm -f "$ROOT/tests/test_runtime_storage_binding_execution.py"
echo "SBP-058 rollback: PASS"
echo "No running blockchain runtime or chain data was modified."
