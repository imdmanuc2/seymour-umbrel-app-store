#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ -d "$REPO/.git" ]] || {
  echo "SBP-015 doctor: FAIL — repository missing" >&2
  exit 1
}

[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] || {
  echo "SBP-015 doctor: FAIL — expected master" >&2
  exit 1
}

for file in   seymour-blockchain-manager/data/web/operations_center.py   seymour-blockchain-manager/data/web/sync_manager.py   seymour-blockchain-manager/data/web/app.py   shared/provider_catalog/providers.v1.json; do
  [[ -f "$REPO/$file" ]] || {
    echo "SBP-015 doctor: FAIL — missing $file" >&2
    exit 1
  }
done

python3 -m py_compile   "$ROOT/payload/nexus_integration.py"   "$ROOT/payload/test_nexus_integration.py"   "$ROOT/payload/test_nexus_api_contract.py"

echo "SBP-015 doctor: PASS"
