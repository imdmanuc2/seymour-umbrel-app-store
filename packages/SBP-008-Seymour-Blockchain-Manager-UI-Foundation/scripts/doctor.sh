#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-008 doctor: FAIL — $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] || fail "Repository not found"
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch"

required=(
  "shared/provider_catalog/providers.v1.json"
  "shared/provider_catalog/catalog.py"
  "scripts/seymour-provider-catalog"
  "seymour-bch-node/docker-compose.yml"
)

for relative in "${required[@]}"; do
  [[ -f "$REPO/$relative" ]] || fail "Missing $relative"
done

python3 -m py_compile \
  "$ROOT/payload/seymour-blockchain-manager/data/web/app.py" \
  "$ROOT/payload/tests/test_blockchain_manager_ui.py" \
  "$ROOT/payload/tests/test_blockchain_manager_catalog.py"

echo "SBP-008 doctor: PASS"
