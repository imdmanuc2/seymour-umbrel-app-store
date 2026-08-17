#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="$(cd "$PKG/../.." && pwd)"
APPJS="$REPO/seymour-blockchain-manager/data/web/app.js"
TEL="$REPO/seymour-blockchain-manager/data/web/telemetry.py"
STATUS="$REPO/seymour-bch-node/data/status/app.py"

echo "SBP-063.3.8 doctor: checking runtime-state/storage telemetry prerequisites"
for f in "$APPJS" "$TEL" "$STATUS"; do
  test -f "$f" || { echo "Missing prerequisite: $f"; exit 1; }
done
python3 -m py_compile "$TEL" "$STATUS"
echo "SBP-063.3.8 Python compile foundation: PASS"
grep -q 'function presentedRuntime(provider)' "$APPJS"
grep -q 'runtime_state = operational_state.get("state")' "$TEL"
grep -q 'def storage_payload()' "$STATUS"
echo "SBP-063.3.8 projection anchors: PASS"
echo "SBP-063.3.8 doctor: PASS"
