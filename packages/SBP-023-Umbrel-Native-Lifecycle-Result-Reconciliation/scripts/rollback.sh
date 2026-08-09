#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -f "$BACKUP/shared/umbrel_control/bridge.py" ]] || {
  echo "Invalid SBP-023 backup: $BACKUP" >&2
  exit 1
}

cp "$BACKUP/shared/umbrel_control/bridge.py" "$ROOT/shared/umbrel_control/bridge.py"
cp "$BACKUP/shared/umbrel_control/native-client.ts" "$ROOT/shared/umbrel_control/native-client.ts"
cp "$BACKUP/seymour-blockchain-manager/data/web/bch_runtime_probe.py" "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"

rm -f   "$ROOT/tests/test_sbp023_runtime_probe.py"   "$ROOT/tests/test_sbp023_lifecycle_contract.py"   "$ROOT/tests/test_sbp023_native_client_contract.py"

echo "SBP-023 rollback: PASS"
