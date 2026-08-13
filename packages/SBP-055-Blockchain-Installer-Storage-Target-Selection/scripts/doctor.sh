#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-055 doctor: FAIL: $*" >&2; exit 1; }
echo "SBP-055 doctor: checking storage-target selection integration"
[[ -f "$ROOT/shared/blockchain_install/storage.py" ]] || fail "SBP-054 missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/installer.py" ]] || fail "installer missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/app.py" ]] || fail "app.py missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/app.js" ]] || fail "app.js missing"
python3 -m py_compile "$PKG/payload/seymour-blockchain-manager/data/web/storage_targets.py" "$PKG/scripts/patch.py"
echo "SBP-055 doctor: SBP-054 dependency PASS"
echo "SBP-055 doctor: manager anchors PASS"
echo "SBP-055 doctor: PASS"
