#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -d "$REPO/.git" ]] || { echo 'SBP-010 doctor: FAIL — repository missing' >&2; exit 1; }
[[ "$(git -C "$REPO" branch --show-current)" == master ]] || { echo 'SBP-010 doctor: FAIL — expected master' >&2; exit 1; }
for f in seymour-blockchain-manager/data/web/app.py seymour-blockchain-manager/data/web/app.js scripts/seymour-umbrel-app shared/umbrel_control/bridge.py; do [[ -f "$REPO/$f" ]] || { echo "missing $f" >&2; exit 1; }; done
python3 -m py_compile "$ROOT/payload/seymour-blockchain-manager/data/web/lifecycle.py" "$ROOT/payload/tests/test_guarded_lifecycle.py"
echo 'SBP-010 doctor: PASS'
