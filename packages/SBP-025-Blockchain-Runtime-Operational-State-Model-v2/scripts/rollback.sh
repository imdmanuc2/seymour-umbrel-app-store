#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -f \
  "$BACKUP/seymour-blockchain-manager/data/web/bch_runtime_probe.py" ]] || {
  echo "Invalid SBP-025 backup: $BACKUP" >&2
  exit 1
}

cp \
  "$BACKUP/seymour-blockchain-manager/data/web/bch_runtime_probe.py" \
  "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"

cp \
  "$BACKUP/seymour-blockchain-manager/data/web/nexus_integration.py" \
  "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py"

if [[ -f \
  "$BACKUP/seymour-blockchain-manager/data/web/runtime_state.py" ]]; then
  cp \
    "$BACKUP/seymour-blockchain-manager/data/web/runtime_state.py" \
    "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py"
else
  rm -f \
    "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py"
fi

rm -f \
  "$ROOT/tests/test_sbp025_runtime_state.py" \
  "$ROOT/tests/test_sbp025_runtime_contract.py"

echo "SBP-025 rollback: PASS"
