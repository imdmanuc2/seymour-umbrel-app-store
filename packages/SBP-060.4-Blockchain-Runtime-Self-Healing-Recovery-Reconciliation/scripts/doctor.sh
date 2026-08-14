#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "SBP-060.4 doctor: checking self-healing recovery prerequisites"
command -v findmnt >/dev/null
command -v mount >/dev/null
python3 -m py_compile "$PKG"/payload/shared/blockchain_recovery/*.py "$PKG"/payload/scripts/seymour-blockchain-heal
echo "SBP-060.4 doctor: recovery model PASS"
echo "SBP-060.4 doctor: bounded repair dependencies PASS"
echo "SBP-060.4 doctor: PASS"
