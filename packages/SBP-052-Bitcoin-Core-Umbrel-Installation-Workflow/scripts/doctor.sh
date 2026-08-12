#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fail(){ echo "SBP-052 doctor: FAIL: $*" >&2; exit 1; }

echo "SBP-052 doctor: checking BTC Umbrel installation workflow"
[[ -f "$ROOT/seymour-bitcoin-node/umbrel-app.yml" ]] || fail "BTC manifest missing"
[[ -f "$ROOT/seymour-bitcoin-node/docker-compose.yml" ]] || fail "BTC compose missing"
[[ -x "$ROOT/scripts/seymour-umbrel-app" ]] || fail "Umbrel control bridge missing"
[[ -f "$PKG/payload/scripts/seymour-install-btc" ]] || fail "workflow payload missing"
grep -Fq 'ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0' "$ROOT/seymour-bitcoin-node/docker-compose.yml" || fail "BTC image reference missing"
python3 -m py_compile "$PKG/payload/scripts/seymour-install-btc"
echo "SBP-052 doctor: BTC app foundation PASS"
echo "SBP-052 doctor: canonical Umbrel bridge PASS"
echo "SBP-052 doctor: guarded install workflow PASS"
echo "SBP-052 doctor: PASS"
