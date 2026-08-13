#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-054 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-054 doctor: checking blockchain install preflight/storage foundation"
[[ -d "$ROOT/shared/provider_catalog" ]] || fail "provider catalog missing"
[[ -f "$PKG/payload/shared/blockchain_install/preflight.py" ]] || fail "preflight module missing"
[[ -f "$PKG/payload/shared/blockchain_install/storage.py" ]] || fail "storage module missing"
python3 -m py_compile "$PKG"/payload/shared/blockchain_install/*.py
python3 -m json.tool "$PKG/payload/shared/contracts/blockchain-install-preflight-v1.json" >/dev/null
echo "SBP-054 doctor: provider-neutral modules PASS"
echo "SBP-054 doctor: storage-target contract PASS"
echo "SBP-054 doctor: PASS"
