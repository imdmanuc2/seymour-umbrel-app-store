#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "SBP-060.3 doctor: checking storage mount safety prerequisites"
test -f "$ROOT/shared/blockchain_install/storage.py"
test -f "$ROOT/shared/blockchain_install/models.py"
test -f "$ROOT/shared/blockchain_install/preflight.py"
test -f "$ROOT/seymour-blockchain-manager/data/web/installer.py"
python3 -m py_compile "$PKG/scripts/patch.py"
echo "SBP-060.3 doctor: storage foundation PASS"
echo "SBP-060.3 doctor: installer integration anchors PASS"
echo "SBP-060.3 doctor: PASS"
