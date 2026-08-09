#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"
[[ -f "$BACKUP/seymour-bch-node/docker-compose.yml" ]] || { echo "Invalid SBP-024 backup: $BACKUP" >&2; exit 1; }
cp "$BACKUP/seymour-bch-node/docker-compose.yml" "$ROOT/seymour-bch-node/docker-compose.yml"
cp "$BACKUP/seymour-bch-node/data/status/app.py" "$ROOT/seymour-bch-node/data/status/app.py"
cp "$BACKUP/shared/umbrel_control/bridge.py" "$ROOT/shared/umbrel_control/bridge.py"
rm -f "$ROOT/tests/test_sbp024_healthcheck_contract.py" "$ROOT/tests/test_sbp024_lifecycle_reconciliation.py" "$ROOT/tests/test_sbp024_status_contract.py"
echo "SBP-024 rollback: PASS"
