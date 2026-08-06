#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -d "$REPO/.git" ]] || { echo "SBP-011 doctor: FAIL — repository missing" >&2; exit 1; }
[[ "$(git -C "$REPO" branch --show-current)" == "master" ]] || { echo "SBP-011 doctor: FAIL — expected master" >&2; exit 1; }
for file in seymour-blockchain-manager/data/web/lifecycle.py seymour-blockchain-manager/data/web/telemetry.py scripts/seymour-install-bch scripts/seymour-umbrel-app; do [[ -f "$REPO/$file" ]] || { echo "SBP-011 doctor: FAIL — missing $file" >&2; exit 1; }; done
python3 -m py_compile "$ROOT/payload/installer.py"
echo "SBP-011 doctor: PASS"
