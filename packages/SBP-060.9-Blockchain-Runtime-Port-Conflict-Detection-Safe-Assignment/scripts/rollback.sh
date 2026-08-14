#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
BACKUP="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-060.9-*' | sort | tail -1)"
test -n "$BACKUP"
cp -a "$BACKUP/models.py" "$ROOT/shared/blockchain_recovery/models.py"
cp -a "$BACKUP/engine.py" "$ROOT/shared/blockchain_recovery/engine.py"
cp -a "$BACKUP/seymour-blockchain-heal" "$ROOT/scripts/seymour-blockchain-heal"
cp -a "$BACKUP/bitcoin-docker-compose.yml" "$ROOT/seymour-bitcoin-node/docker-compose.yml"
rm -f "$ROOT/shared/blockchain_recovery/port_guard.py" "$ROOT/tests/test_port_conflict.py"
echo "SBP-060.9 rollback: PASS"
