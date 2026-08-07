#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}";ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -d "$REPO/.git" ]] || { echo "SBP-014 doctor: FAIL — repository missing" >&2; exit 1; }
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] || { echo "SBP-014 doctor: FAIL — expected master" >&2; exit 1; }
for f in seymour-blockchain-manager/data/web/adoption.py seymour-blockchain-manager/data/web/sync_manager.py seymour-blockchain-manager/data/web/lifecycle.py;do [[ -f "$REPO/$f" ]]||{ echo "SBP-014 doctor: FAIL — missing $f" >&2;exit 1;};done
python3 -m py_compile "$ROOT/payload/seymour-blockchain-manager/data/web/operations_center.py" "$ROOT/payload/tests/test_operations_center.py" "$ROOT/payload/tests/test_operations_center_ui.py"
echo "SBP-014 doctor: PASS"
