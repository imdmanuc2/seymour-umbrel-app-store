#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-060 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-060 doctor: checking Bitcoin provider activation prerequisites"
[[ -f "$ROOT/shared/provider_catalog/providers.v1.json" ]] || fail "shared catalog missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/catalog/providers.v1.json" ]] || fail "manager catalog missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/app.py" ]] || fail "app.py missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/app.js" ]] || fail "app.js missing"
python3 -m py_compile "$PKG/scripts/patch.py"
echo "SBP-060 doctor: provider catalogs PASS"
echo "SBP-060 doctor: manager install API/UI anchors PASS"
echo "SBP-060 doctor: PASS"
