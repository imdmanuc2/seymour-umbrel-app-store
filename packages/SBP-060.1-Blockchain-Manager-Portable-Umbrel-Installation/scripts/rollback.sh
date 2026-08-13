#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-060.1-latest"
[[ -f "$LATEST" ]] || { echo "SBP-060.1 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"

cp -a "$BACKUP/seymour-blockchain-manager/docker-compose.yml"   "$ROOT/seymour-blockchain-manager/docker-compose.yml"
rm -rf   "$ROOT/seymour-blockchain-manager/data/control"   "$ROOT/seymour-blockchain-manager/data/shared"
rm -f "$ROOT/tests/test_blockchain_manager_portable_install.py"

echo "SBP-060.1 rollback: PASS"
echo "No installed Umbrel app or blockchain runtime was modified."
