#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "SBP-060.2 doctor: checking proxy DNS readiness prerequisites"
test -f "$ROOT/seymour-blockchain-manager/docker-compose.yml"
grep -q 'APP_PORT: 8080' "$ROOT/seymour-blockchain-manager/docker-compose.yml"
python3 -m py_compile "$PKG/scripts/patch.py"
echo "SBP-060.2 doctor: compose PASS"
echo "SBP-060.2 doctor: backend port contract PASS"
echo "SBP-060.2 doctor: PASS"
