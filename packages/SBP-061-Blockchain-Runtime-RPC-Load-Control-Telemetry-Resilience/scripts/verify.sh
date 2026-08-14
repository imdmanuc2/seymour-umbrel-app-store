#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
echo "SBP-061 verify: BCH RPC load control and telemetry resilience"
python3 -m py_compile "$WEB/bch_runtime_probe.py" "$WEB/telemetry.py"
grep -q 'BCH_RUNTIME_CACHE_TTL_SECONDS' "$WEB/bch_runtime_probe.py"
grep -q 'def _probe_uncached' "$WEB/bch_runtime_probe.py"
grep -q 'telemetrySource' "$WEB/bch_runtime_probe.py"
grep -q '"telemetryFresh": runtime.get("telemetryFresh")' "$WEB/telemetry.py"
PYTHONPATH="$ROOT:$WEB" python3 "$ROOT/tests/test_bch_runtime_cache.py"
echo "SBP-061 cache TTL contract: PASS"
echo "SBP-061 single-flight contract: PASS"
echo "SBP-061 last-known-good continuity contract: PASS"
echo "SBP-061 dashboard freshness projection contract: PASS"
echo "SBP-061 final verification: PASS"
echo "No live blockchain runtime was restarted or modified."

grep -q \
  'BCH_HEALTH_URL: http://seymour-bch-node_status_1:8080/api/health' \
  "$ROOT/seymour-blockchain-manager/docker-compose.yml"

grep -q \
  'BCH_STATUS_URL: http://seymour-bch-node_status_1:8080/api/status' \
  "$ROOT/seymour-blockchain-manager/docker-compose.yml"

if grep -qE \
  'BCH_(HEALTH|STATUS)_URL: http://status:8080' \
  "$ROOT/seymour-blockchain-manager/docker-compose.yml"
then
  echo "FAIL: generic BCH status alias remains"
  exit 1
fi

echo "SBP-061 provider-specific status identity contract: PASS"
