#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "SBP-064 doctor: checking runtime health guidance prerequisites"
for f in "$REPO/seymour-blockchain-manager/data/web/telemetry.py" "$REPO/seymour-blockchain-manager/data/web/app.js" "$REPO/seymour-blockchain-manager/data/web/operations_center.py" "$PKG/payload/seymour-blockchain-manager/data/web/runtime_health.py"; do test -f "$f" || { echo "ERROR: missing $f"; exit 1; }; done
python3 -m py_compile "$PKG/payload/seymour-blockchain-manager/data/web/runtime_health.py"
echo "SBP-064 health projection compile contract: PASS"
grep -q 'Run diagnostics' "$REPO/seymour-blockchain-manager/data/web/app.js"
grep -q 'recommendations' "$REPO/seymour-blockchain-manager/data/web/operations_center.py"
echo "SBP-064 existing operations integration anchors: PASS"
echo "SBP-064 doctor: PASS"
