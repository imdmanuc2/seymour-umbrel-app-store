#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -d "$ROOT/.git" ]] || { echo "SBP-025 doctor: FAIL — repository not found"; exit 1; }
[[ "$(git -C "$ROOT" branch --show-current)" == "master" ]] || { echo "SBP-025 doctor: FAIL — expected master branch"; exit 1; }
for file in seymour-blockchain-manager/data/web/bch_runtime_probe.py seymour-blockchain-manager/data/web/nexus_integration.py; do
  [[ -f "$ROOT/$file" ]] || { echo "SBP-025 doctor: FAIL — missing $file"; exit 1; }
done
python3 -m py_compile "$PKG/payload/runtime_state.py" "$PKG/payload/patch_runtime_probe.py" "$PKG/payload/patch_nexus_integration.py"
echo "SBP-025 doctor: PASS"
