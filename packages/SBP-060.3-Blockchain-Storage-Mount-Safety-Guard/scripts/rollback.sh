#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-060.3-latest"
test -f "$LATEST"
BACKUP="$(cat "$LATEST")"
for f in models.py storage.py preflight.py __init__.py; do cp -a "$BACKUP/shared/blockchain_install/$f" "$ROOT/shared/blockchain_install/$f"; done
cp -a "$BACKUP/seymour-blockchain-manager/data/web/storage_targets.py" "$ROOT/seymour-blockchain-manager/data/web/storage_targets.py"
cp -a "$BACKUP/seymour-blockchain-manager/data/web/installer.py" "$ROOT/seymour-blockchain-manager/data/web/installer.py"
rm -f "$ROOT/tests/test_blockchain_storage_mount_guard.py"
echo "SBP-060.3 rollback: PASS"
echo "No running blockchain runtime or chain data was modified."
