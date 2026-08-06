#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-009 doctor: FAIL — $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] || fail "Repository not found"
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch"

required=(
  "seymour-blockchain-manager/data/web/app.py"
  "seymour-blockchain-manager/data/web/app.js"
  "seymour-blockchain-manager/data/web/style.css"
  "shared/provider_catalog/providers.v1.json"
)

for relative in "${required[@]}"; do
  [[ -f "$REPO/$relative" ]] || fail "Missing $relative"
done

python3 -m py_compile \
  "$ROOT/payload/seymour-blockchain-manager/data/web/telemetry.py" \
  "$ROOT/payload/seymour-blockchain-manager/data/web/app.py" \
  "$ROOT/payload/tests/test_live_dashboard.py" \
  "$ROOT/payload/tests/test_live_dashboard_contract.py"

echo "SBP-009 doctor: PASS"
