#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-023 doctor: FAIL — $*" >&2; exit 1; }

[[ -d "$ROOT/.git" ]] || fail "Umbrel app-store repository not found"
[[ "$(git -C "$ROOT" branch --show-current)" == "master" ]] || fail "Expected master branch"

for file in   shared/umbrel_control/bridge.py   shared/umbrel_control/native-client.ts   seymour-blockchain-manager/data/web/bch_runtime_probe.py; do
  [[ -f "$ROOT/$file" ]] || fail "Missing $file"
done

python3 -m py_compile "$PKG/payload/patch_lifecycle_bridge.py" "$PKG/payload/patch_runtime_probe.py"
echo "SBP-023 doctor: PASS"
