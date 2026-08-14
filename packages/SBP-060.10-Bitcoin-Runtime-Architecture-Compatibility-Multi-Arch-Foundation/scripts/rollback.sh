#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
BACKUP="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-060.10-*' | sort | tail -1)"
test -n "$BACKUP"

cp -a "$BACKUP/models.py" "$ROOT/shared/blockchain_recovery/models.py"
cp -a "$BACKUP/engine.py" "$ROOT/shared/blockchain_recovery/engine.py"
cp -a "$BACKUP/seymour-blockchain-heal" "$ROOT/scripts/seymour-blockchain-heal"
cp -a "$BACKUP/seymour-bitcoin-managed-runtime" "$ROOT/scripts/seymour-bitcoin-managed-runtime"

rm -f   "$ROOT/shared/bitcoin_managed_runtime/architecture.py"   "$ROOT/shared/blockchain_recovery/image_architecture.py"   "$ROOT/scripts/seymour-bitcoin-architecture-preflight"   "$ROOT/tests/test_bitcoin_architecture_guard.py"

echo "SBP-060.10 rollback: PASS"
echo "No blockchain runtime or blockchain data was modified."
