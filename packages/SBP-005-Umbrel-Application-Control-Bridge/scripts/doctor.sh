#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-005 DOCTOR FAIL: $*" >&2
  exit 1
}

[[ -d "$REPO/.git" ]] \
  || fail "Not a Git repository."

[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] \
  || fail "Expected master branch."

[[ -f "$REPO/shared/umbrel_runtime/runtime.py" ]] \
  || fail "Missing SBP-004 runtime integration."

[[ -f /opt/umbreld/source/modules/jwt.ts ]] \
  || fail "Umbrel JWT module not found."

[[ -f /home/umbrel/umbrel/secrets/jwt ]] \
  || fail "Umbrel JWT secret not found."

command -v /usr/local/bin/node >/dev/null \
  || fail "Umbrel Node runtime not found."

python3 -m py_compile \
  "$ROOT/tests/verify.py" \
  "$ROOT/payload/shared/umbrel_control/bridge.py" \
  "$ROOT/payload/scripts/seymour-umbrel-app"

echo "SBP-005 doctor: PASS"
