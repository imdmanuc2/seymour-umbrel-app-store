#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -d "$BACKUP/seymour-blockchain-manager" ]] || {
  echo "Invalid backup: $BACKUP" >&2
  exit 1
}

rm -rf "$REPO/seymour-blockchain-manager"
cp -a "$BACKUP/seymour-blockchain-manager" "$REPO/"

rm -f   "$REPO/tests/test_nexus_integration.py"   "$REPO/tests/test_nexus_api_contract.py"

echo "SBP-015 rollback: PASS"
