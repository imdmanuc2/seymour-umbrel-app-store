#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-056-$STAMP"
mkdir -p "$BACKUP"

[[ ! -f "$ROOT/shared/blockchain_install/binding.py" ]] || cp -a "$ROOT/shared/blockchain_install/binding.py" "$BACKUP/"
[[ ! -f "$ROOT/shared/blockchain_install/__init__.py" ]] || cp -a "$ROOT/shared/blockchain_install/__init__.py" "$BACKUP/"
[[ ! -f "$ROOT/shared/contracts/blockchain-storage-binding-plan-v1.json" ]] || cp -a "$ROOT/shared/contracts/blockchain-storage-binding-plan-v1.json" "$BACKUP/"
[[ ! -f "$ROOT/tests/test_blockchain_storage_binding.py" ]] || cp -a "$ROOT/tests/test_blockchain_storage_binding.py" "$BACKUP/"

cp "$PKG/payload/shared/blockchain_install/binding.py" "$ROOT/shared/blockchain_install/binding.py"

if ! grep -Fq 'from .binding import StorageBindingPlan' "$ROOT/shared/blockchain_install/__init__.py"; then
  cat "$PKG/payload/shared/blockchain_install/__init__.append" >> "$ROOT/shared/blockchain_install/__init__.py"
fi

cp "$PKG/payload/shared/contracts/blockchain-storage-binding-plan-v1.json" "$ROOT/shared/contracts/"
cp "$PKG/payload/tests/test_blockchain_storage_binding.py" "$ROOT/tests/"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-056-latest"

echo "Backup: $BACKUP"
echo "SBP-056 storage binding model installed: PASS"
echo "SBP-056 provider data-path plan installed: PASS"
echo "SBP-056 install: PASS"
echo "No blockchain data was moved."
echo "No mount, NFS, SMB, Docker, or Umbrel lifecycle change was executed."
