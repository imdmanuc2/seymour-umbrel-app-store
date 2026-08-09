#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -f "$BACKUP/seymour-blockchain-manager/data/web/nexus_integration.py" ]] || {
  echo "Invalid SBP-026 backup: $BACKUP" >&2
  exit 1
}

cp \
  "$BACKUP/seymour-blockchain-manager/data/web/nexus_integration.py" \
  "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"

rm -f \
  "$ROOT/tests/test_sbp026_projection_contract.py" \
  "$ROOT/tests/test_sbp026_runtime_state_values.py"

echo "SBP-026 rollback: PASS"
