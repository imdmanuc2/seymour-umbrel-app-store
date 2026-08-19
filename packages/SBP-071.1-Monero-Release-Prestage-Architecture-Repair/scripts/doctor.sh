#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
WF="$REPO/.github/workflows/seymour-monero-node-multiarch.yml"

echo "SBP-071.1 doctor: checking Monero workflow repair prerequisites"

test -f "$WF"
python3 -m py_compile "$(dirname "${BASH_SOURCE[0]}")/patch.py"

grep -q 'monero-linux-armv8-v0.18.5.1.tar.bz2' "$WF"
grep -q 'c0caf042cb7c7b760f5ad6be188084b59352440b32990a78b8051497b9398dbc' "$WF"
grep -q 'docker/setup-qemu-action@v3' "$WF"
grep -q 'Smoke-test architecture image' "$WF"

echo "SBP-071.1 workflow prerequisites: PASS"
echo "SBP-071.1 doctor: PASS"
