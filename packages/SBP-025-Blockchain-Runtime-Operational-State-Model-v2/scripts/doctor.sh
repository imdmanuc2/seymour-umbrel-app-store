#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "SBP-025 doctor: FAIL — $*" >&2
  exit 1
}

[[ -d "$ROOT/.git" ]] \
  || fail "Umbrel app-store repository not found"

[[ "$(git -C "$ROOT" branch --show-current)" == "master" ]] \
  || fail "Expected master branch"

for file in \
  seymour-blockchain-manager/data/web/bch_runtime_probe.py \
  seymour-blockchain-manager/data/web/nexus_integration.py; do
  [[ -f "$ROOT/$file" ]] \
    || fail "Missing $file"
done

python3 -m py_compile \
  "$PKG/payload/runtime_state.py" \
  "$PKG/payload/patch_runtime_probe.py" \
  "$PKG/payload/patch_nexus_integration.py"

echo "SBP-025 doctor: PASS"
