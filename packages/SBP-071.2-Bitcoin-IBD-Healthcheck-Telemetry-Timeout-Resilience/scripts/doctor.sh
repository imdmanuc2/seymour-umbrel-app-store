#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

COMPOSE="$REPO/seymour-bitcoin-node/docker-compose.yml"
STATUS="$REPO/seymour-bitcoin-node/data/status/app.py"
PATCH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/patch.py"

echo "SBP-071.2 doctor: checking Bitcoin IBD observer prerequisites"

for f in "$COMPOSE" "$STATUS" "$PATCH"; do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done

python3 -m py_compile "$STATUS" "$PATCH"

grep -q 'rpcwaittimeout=5' "$COMPOSE"
grep -q 'HEAVY_TIMEOUT' "$STATUS"
grep -q 'def reachability' "$STATUS"
grep -q 'telemetryStale' "$STATUS"
grep -q 'live-cache' "$STATUS"

echo "SBP-071.2 existing health/telemetry contracts: PASS"
echo "SBP-071.2 doctor: PASS"
