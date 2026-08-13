#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-057-latest"
[[ -f "$LATEST" ]] || { echo "SBP-057 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"

rm -f   "$ROOT/shared/blockchain_install/materialize.py"   "$ROOT/scripts/seymour-storage-materialize"   "$ROOT/shared/contracts/blockchain-storage-materialization-v1.json"   "$ROOT/tests/test_remote_storage_materialization.py"

[[ ! -f "$BACKUP/materialize.py" ]] || cp -a "$BACKUP/materialize.py" "$ROOT/shared/blockchain_install/"
[[ ! -f "$BACKUP/__init__.py" ]] || cp -a "$BACKUP/__init__.py" "$ROOT/shared/blockchain_install/__init__.py"
[[ ! -f "$BACKUP/seymour-storage-materialize" ]] || cp -a "$BACKUP/seymour-storage-materialize" "$ROOT/scripts/"
[[ ! -f "$BACKUP/blockchain-storage-materialization-v1.json" ]] || cp -a "$BACKUP/blockchain-storage-materialization-v1.json" "$ROOT/shared/contracts/"

echo "SBP-057 rollback: PASS"
echo "No configured NFS export or runtime mount was changed by rollback."
