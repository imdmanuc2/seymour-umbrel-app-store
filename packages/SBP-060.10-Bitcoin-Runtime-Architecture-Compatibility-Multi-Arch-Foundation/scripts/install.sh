#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-060.10-$STAMP"
mkdir -p "$BACKUP" "$ROOT/tests"

cp -a "$ROOT/shared/blockchain_recovery/models.py" "$BACKUP/models.py"
cp -a "$ROOT/shared/blockchain_recovery/engine.py" "$BACKUP/engine.py"
cp -a "$ROOT/scripts/seymour-blockchain-heal" "$BACKUP/seymour-blockchain-heal"
cp -a "$ROOT/scripts/seymour-bitcoin-managed-runtime" "$BACKUP/seymour-bitcoin-managed-runtime"

cp "$PKG/payload/shared/bitcoin_managed_runtime/architecture.py"    "$ROOT/shared/bitcoin_managed_runtime/architecture.py"

cp "$PKG/payload/shared/blockchain_recovery/image_architecture.py"    "$ROOT/shared/blockchain_recovery/image_architecture.py"

cp "$PKG/payload/seymour-bitcoin-architecture-preflight"    "$ROOT/scripts/seymour-bitcoin-architecture-preflight"

cp "$PKG/payload/tests/test_bitcoin_architecture_guard.py"    "$ROOT/tests/test_bitcoin_architecture_guard.py"

chmod +x   "$ROOT/scripts/seymour-bitcoin-architecture-preflight"   "$ROOT/scripts/seymour-bitcoin-managed-runtime"   "$ROOT/scripts/seymour-blockchain-heal"

python3 "$PKG/scripts/patch.py"

echo "Backup: $BACKUP"
echo "SBP-060.10 architecture preflight installed: PASS"
echo "SBP-060.10 recovery classification installed: PASS"
echo "SBP-060.10 guarded Bitcoin wrapper installed: PASS"
echo "SBP-060.10 multi-arch image contract installed: PASS"
echo "SBP-060.10 install: PASS"
echo "No blockchain runtime was restarted and no blockchain data was modified."
