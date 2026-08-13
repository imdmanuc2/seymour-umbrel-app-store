#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-057-$STAMP"
mkdir -p "$BACKUP"

[[ ! -f "$ROOT/shared/blockchain_install/materialize.py" ]] || cp -a "$ROOT/shared/blockchain_install/materialize.py" "$BACKUP/"
[[ ! -f "$ROOT/shared/blockchain_install/__init__.py" ]] || cp -a "$ROOT/shared/blockchain_install/__init__.py" "$BACKUP/"
[[ ! -f "$ROOT/scripts/seymour-storage-materialize" ]] || cp -a "$ROOT/scripts/seymour-storage-materialize" "$BACKUP/"
[[ ! -f "$ROOT/shared/contracts/blockchain-storage-materialization-v1.json" ]] || cp -a "$ROOT/shared/contracts/blockchain-storage-materialization-v1.json" "$BACKUP/"

cp "$PKG/payload/shared/blockchain_install/materialize.py"   "$ROOT/shared/blockchain_install/materialize.py"

if ! grep -Fq 'from .materialize import NfsMaterializationPlan' "$ROOT/shared/blockchain_install/__init__.py"; then
  cat "$PKG/payload/shared/blockchain_install/__init__.append" >>     "$ROOT/shared/blockchain_install/__init__.py"
fi

cp "$PKG/payload/scripts/seymour-storage-materialize"   "$ROOT/scripts/seymour-storage-materialize"
chmod +x "$ROOT/scripts/seymour-storage-materialize"

cp "$PKG/payload/shared/contracts/blockchain-storage-materialization-v1.json"   "$ROOT/shared/contracts/"

cp "$PKG/payload/tests/test_remote_storage_materialization.py"   "$ROOT/tests/"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-057-latest"

echo "Backup: $BACKUP"
echo "SBP-057 NFS materialization engine installed: PASS"
echo "SBP-057 guarded storage CLI installed: PASS"
echo "SBP-057 install: PASS"
echo "No NFS export, mount, fstab, blockchain runtime, or chain data was modified."
