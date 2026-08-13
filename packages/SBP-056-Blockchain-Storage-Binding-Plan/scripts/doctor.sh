#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-056 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-056 doctor: checking blockchain storage binding foundation"
[[ -f "$ROOT/shared/blockchain_install/models.py" ]] || fail "SBP-054 models missing"
[[ -f "$ROOT/seymour-blockchain-manager/data/web/storage_targets.py" ]] || fail "SBP-055 storage selection missing"
python3 -m py_compile "$PKG/payload/shared/blockchain_install/binding.py"
python3 -m json.tool "$PKG/payload/shared/contracts/blockchain-storage-binding-plan-v1.json" >/dev/null
echo "SBP-056 doctor: dependencies PASS"
echo "SBP-056 doctor: binding contract PASS"
echo "SBP-056 doctor: PASS"
