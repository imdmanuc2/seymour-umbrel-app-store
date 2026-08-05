#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-003 DOCTOR FAIL: $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] \
  || fail "Not a Git repository."

[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch."

[[ "$(git -C "$REPO" rev-parse --short HEAD)" == "a37ddd5" ]] \
  || fail "Expected SBP-002 baseline a37ddd5."

required=(
  "seymour-bch-node/umbrel-app.yml"
  "seymour-bch-node/docker-compose.yml"
  "seymour-bch-node/data/status/app.py"
  "seymour-bch-node/data/status/provisioning.py"
  "seymour-bch-node/data/status/templates/provision.html"
  "seymour-bch-node/data/node/entrypoint.sh"
)

for relative in "${required[@]}"; do
  [[ -f "$REPO/$relative" ]] \
    || fail "Missing SBP-002 prerequisite: $relative"
done

grep -q "/api/provisioning/plan" \
  "$REPO/seymour-bch-node/data/status/app.py" \
  || fail "SBP-002 plan endpoint missing."

python3 -m py_compile \
  "$ROOT/tests/verify.py" \
  "$ROOT/payload/seymour-bch-node/data/status/app.py" \
  "$ROOT/payload/seymour-bch-node/data/status/provisioning.py"

echo "SBP-003 doctor: PASS"
