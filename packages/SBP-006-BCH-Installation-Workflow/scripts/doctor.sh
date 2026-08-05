#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(
  cd "$(dirname "${BASH_SOURCE[0]}")/.."
  pwd
)"

fail() {
  echo "SBP-006 DOCTOR FAIL: $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] \
  || fail "Not a Git repository."

[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch."

required=(
  "scripts/seymour-umbrel-app"
  "scripts/seymour-umbrel-runtime"
  "shared/umbrel_control/bridge.py"
  "shared/umbrel_runtime/runtime.py"
  "seymour-bch-node/umbrel-app.yml"
)

for relative in "${required[@]}"; do
  [[ -f "$REPO/$relative" ]] \
    || fail "Missing prerequisite: $relative"
done

grep -q 'version: "0.2.0-alpha"' \
  "$REPO/seymour-bch-node/umbrel-app.yml" \
  || fail "Unexpected BCH app version."

python3 -m py_compile \
  "$ROOT/tests/verify.py" \
  "$ROOT/payload/shared/bch_install/workflow.py" \
  "$ROOT/payload/scripts/seymour-install-bch"

echo "SBP-006 doctor: PASS"
