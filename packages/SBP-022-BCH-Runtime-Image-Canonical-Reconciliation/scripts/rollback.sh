#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"
[[ -f "$BACKUP/seymour-bch-node/docker-compose.yml" ]] || { echo "Invalid SBP-022 backup: $BACKUP" >&2; exit 1; }
cp "$BACKUP/seymour-bch-node/docker-compose.yml" "$ROOT/seymour-bch-node/docker-compose.yml"
cp "$BACKUP/seymour-bch-node/data/node/entrypoint.sh" "$ROOT/seymour-bch-node/data/node/entrypoint.sh"
rm -f "$ROOT/tests/test_bch_canonical_entrypoint.py" "$ROOT/tests/test_bch_recreation_contract.py" "$ROOT/tests/test_bch_healthcheck_contract.py"
echo "SBP-022 rollback: PASS"
