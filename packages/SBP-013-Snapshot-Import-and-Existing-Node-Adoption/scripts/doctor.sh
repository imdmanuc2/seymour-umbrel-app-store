#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -d "$REPO/.git" ]] || { echo "SBP-013 doctor: FAIL — repository missing" >&2; exit 1; }
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] || { echo "SBP-013 doctor: FAIL — expected master" >&2; exit 1; }
for file in seymour-blockchain-manager/data/web/sync_manager.py seymour-blockchain-manager/data/web/installer.py seymour-blockchain-manager/data/web/app.py; do
  [[ -f "$REPO/$file" ]] || { echo "SBP-013 doctor: FAIL — missing $file" >&2; exit 1; }
done
python3 -m py_compile "$ROOT/payload/seymour-blockchain-manager/data/web/adoption.py" "$ROOT/payload/tests/test_adoption.py" "$ROOT/payload/tests/test_adoption_ui.py"
echo "SBP-013 doctor: PASS"
