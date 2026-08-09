#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail(){ echo "SBP-026 doctor: FAIL — $*" >&2; exit 1; }

[[ -d "$ROOT/.git" ]] || fail "Umbrel app-store repository not found"
[[ "$(git -C "$ROOT" branch --show-current)" == "master" ]] || fail "Expected master branch"

for file in \
  seymour-blockchain-manager/data/web/nexus_integration.py \
  seymour-blockchain-manager/data/web/runtime_state.py; do
  [[ -f "$ROOT/$file" ]] || fail "Missing $file"
done

grep -q 'telemetry\["operationalState"\]' \
  "$ROOT/seymour-blockchain-manager/data/web/nexus_integration.py" \
  || fail "SBP-025 operational-state projection not found"

python3 -m py_compile "$PKG/payload/patch_nexus_state_projection.py"
echo "SBP-026 doctor: PASS"
