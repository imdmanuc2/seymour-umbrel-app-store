#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
LATEST="$ROOT/backups/sbp-056-latest"
[[ -f "$LATEST" ]] || { echo "SBP-056 rollback: backup pointer missing" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"

rm -f   "$ROOT/shared/blockchain_install/binding.py"   "$ROOT/shared/contracts/blockchain-storage-binding-plan-v1.json"   "$ROOT/tests/test_blockchain_storage_binding.py"

if [[ -f "$BACKUP/binding.py" ]]; then cp -a "$BACKUP/binding.py" "$ROOT/shared/blockchain_install/"; fi
if [[ -f "$BACKUP/__init__.py" ]]; then cp -a "$BACKUP/__init__.py" "$ROOT/shared/blockchain_install/__init__.py"; fi
if [[ -f "$BACKUP/blockchain-storage-binding-plan-v1.json" ]]; then cp -a "$BACKUP/blockchain-storage-binding-plan-v1.json" "$ROOT/shared/contracts/"; fi
if [[ -f "$BACKUP/test_blockchain_storage_binding.py" ]]; then cp -a "$BACKUP/test_blockchain_storage_binding.py" "$ROOT/tests/"; fi

echo "SBP-056 rollback: PASS"
echo "No running blockchain runtime or chain data was modified."
