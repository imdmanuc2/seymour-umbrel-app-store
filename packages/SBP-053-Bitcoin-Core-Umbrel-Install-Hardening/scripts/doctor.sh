#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-053 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-053 doctor: checking Bitcoin Core install hardening prerequisites"
[[ -f "$ROOT/seymour-bitcoin-node/data/node/entrypoint.sh" ]] || fail "BTC entrypoint missing"
[[ -f "$ROOT/scripts/seymour-install-btc" ]] || fail "BTC installer missing"
[[ -f "$PKG/payload/seymour-bitcoin-node/data/generated/.gitkeep" ]] || fail "generated marker missing"
[[ -f "$PKG/payload/seymour-bitcoin-node/data/state/.gitkeep" ]] || fail "state marker missing"
grep -Fq 'APP_ID = "seymour-bitcoin-node"' "$ROOT/scripts/seymour-install-btc" || fail "unexpected BTC installer"
python3 -m py_compile "$ROOT/scripts/seymour-install-btc"
python3 -m py_compile "$PKG/scripts/patch-installer.py"
echo "SBP-053 doctor: BTC runtime files PASS"
echo "SBP-053 doctor: installer contract PASS"
echo "SBP-053 doctor: persistent directory markers PASS"
echo "SBP-053 doctor: PASS"
