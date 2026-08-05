#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-004 DOCTOR FAIL: $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] \
  || fail "Not a Git repository."

[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch."

[[ "$(git -C "$REPO" rev-parse --short HEAD)" == "cad8822" ]] \
  || fail "Expected SBP-003 baseline cad8822."

required=(
  "seymour-bch-node/umbrel-app.yml"
  "seymour-bch-node/docker-compose.yml"
  "seymour-bch-node/data/status/app.py"
  "seymour-bch-node/data/status/provisioning.py"
)

for relative in "${required[@]}"; do
  [[ -f "$REPO/$relative" ]] \
    || fail "Missing SBP-003 prerequisite: $relative"
done

python3 -m py_compile \
  "$ROOT/tests/verify.py" \
  "$ROOT/payload/shared/umbrel_runtime/models.py" \
  "$ROOT/payload/shared/umbrel_runtime/runtime.py" \
  "$ROOT/payload/shared/umbrel_runtime/cli.py"

echo "SBP-004 doctor: PASS"
