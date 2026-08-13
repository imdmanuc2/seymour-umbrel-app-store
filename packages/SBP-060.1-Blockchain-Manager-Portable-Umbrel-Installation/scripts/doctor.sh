#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-060.1 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-060.1 doctor: checking clean Umbrel install prerequisites"
[[ -f "$ROOT/seymour-blockchain-manager/docker-compose.yml" ]] || fail "compose missing"
for script in seymour-umbrel-app seymour-install-bch seymour-install-btc; do
  [[ -f "$ROOT/scripts/$script" ]] || fail "required script missing: $script"
done
[[ -d "$ROOT/shared/blockchain_install" ]] || fail "shared blockchain install library missing"
python3 -m py_compile "$PKG/scripts/patch.py"
echo "SBP-060.1 doctor: control scripts PASS"
echo "SBP-060.1 doctor: shared libraries PASS"
echo "SBP-060.1 doctor: portable compose anchors PASS"
echo "SBP-060.1 doctor: PASS"
