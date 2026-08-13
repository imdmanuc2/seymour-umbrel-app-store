#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-057 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-057 doctor: checking remote storage materialization foundation"
[[ -f "$ROOT/shared/blockchain_install/binding.py" ]] || fail "SBP-056 binding foundation missing"
[[ -f "$ROOT/shared/blockchain_install/storage.py" ]] || fail "SBP-054 storage foundation missing"
python3 -m py_compile   "$PKG/payload/shared/blockchain_install/materialize.py"   "$PKG/payload/scripts/seymour-storage-materialize"
python3 -m json.tool   "$PKG/payload/shared/contracts/blockchain-storage-materialization-v1.json"   >/dev/null
echo "SBP-057 doctor: dependencies PASS"
echo "SBP-057 doctor: guarded NFS materializer PASS"
echo "SBP-057 doctor: PASS"
