#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-016 doctor: FAIL — $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] || fail "Repository not found"

[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch"

for file in \
  seymour-blockchain-manager/data/web/nexus_integration.py \
  seymour-blockchain-manager/data/web/app.py \
  seymour-blockchain-manager/docker-compose.yml; do
  [[ -f "$REPO/$file" ]] || fail "Missing $file"
done

python3 -m py_compile \
  "$ROOT/payload/nexus_delivery.py" \
  "$ROOT/payload/test_nexus_delivery.py" \
  "$ROOT/payload/test_nexus_delivery_retry.py" \
  "$ROOT/payload/test_nexus_delivery_api.py"

echo "SBP-016 doctor: PASS"
