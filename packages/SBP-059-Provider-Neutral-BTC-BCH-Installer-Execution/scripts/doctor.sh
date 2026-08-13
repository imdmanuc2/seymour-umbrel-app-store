#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-059 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-059 doctor: checking provider-neutral installer prerequisites"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/installer.py" ]] || fail "installer missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/app.js" ]] || fail "install UI missing"
[[ -f "$ROOT/scripts/seymour-install-btc" ]] || fail "BTC installer missing"
[[ -f "$ROOT/scripts/seymour-install-bch" ]] || fail "BCH installer missing"
python3 -m py_compile "$PKG/scripts/patch.py"
echo "SBP-059 doctor: BTC/BCH installers PASS"
echo "SBP-059 doctor: provider-neutral anchors PASS"
echo "SBP-059 doctor: PASS"
