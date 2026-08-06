#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-007 doctor: FAIL — $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] || fail "Repository not found"
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch"

required=(
  "seymour-bch-node/docker-compose.yml"
  "seymour-bch-node/umbrel-app.yml"
  "shared/bch_install/workflow.py"
  "scripts/seymour-umbrel-app"
)

for relative in "${required[@]}"; do
  [[ -f "$REPO/$relative" ]] || fail "Missing $relative"
done

python3 -m py_compile \
  "$ROOT/payload/shared/provider_catalog/catalog.py" \
  "$ROOT/payload/scripts/seymour-provider-catalog" \
  "$ROOT/payload/tests/test_provider_catalog.py" \
  "$ROOT/payload/tests/test_bch_catalog_compatibility.py"

python3 -m json.tool \
  "$ROOT/payload/shared/provider_catalog/providers.v1.json" \
  >/dev/null

echo "SBP-007 doctor: PASS"
