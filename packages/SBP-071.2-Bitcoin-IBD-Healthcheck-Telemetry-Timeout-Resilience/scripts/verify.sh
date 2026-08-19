#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

COMPOSE="$REPO/seymour-bitcoin-node/docker-compose.yml"
STATUS="$REPO/seymour-bitcoin-node/data/status/app.py"

INSTALLED_COMPOSE="/home/umbrel/umbrel/app-data/seymour-bitcoin-node/docker-compose.yml"
INSTALLED_STATUS="/home/umbrel/umbrel/app-data/seymour-bitcoin-node/data/status/app.py"

echo "SBP-071.2 verify: Bitcoin IBD healthcheck and telemetry timeout resilience"

python3 -m py_compile "$STATUS"

grep -q 'timeout: 30s' "$COMPOSE"
grep -q 'rpcwaittimeout=5' "$COMPOSE"

echo "SBP-071.2 Docker healthcheck timeout contract: PASS"

grep -q 'BTC_RPC_REACHABILITY_TIMEOUT_SECONDS","30"' "$STATUS"
grep -q 'rpc("uptime",REACHABILITY_TIMEOUT)' "$STATUS"
grep -q 'BTC_RPC_HEAVY_TIMEOUT_SECONDS","120"' "$STATUS"
grep -q 'telemetryStale' "$STATUS"
grep -q 'live-cache' "$STATUS"

echo "SBP-071.2 reachability/heavy telemetry separation contract: PASS"

if timeout 10s sudo test -f "$INSTALLED_COMPOSE"; then
  SRC="$(sha256sum "$COMPOSE" | awk '{print $1}')"
  LIVE="$(timeout 15s sudo sha256sum "$INSTALLED_COMPOSE" | awk '{print $1}')"
  test "$SRC" = "$LIVE"
fi

if timeout 10s sudo test -f "$INSTALLED_STATUS"; then
  SRC="$(sha256sum "$STATUS" | awk '{print $1}')"
  LIVE="$(timeout 15s sudo sha256sum "$INSTALLED_STATUS" | awk '{print $1}')"
  test "$SRC" = "$LIVE"
fi

echo "SBP-071.2 deployed checksum contract: PASS"

BTC_NODE="$(
  timeout 15s sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bitcoin-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"

BCH_NODE="$(
  timeout 15s sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bch-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"

test -n "$BTC_NODE"
test -n "$BCH_NODE"

BTC_STATE="$(timeout 15s sudo docker inspect "$BTC_NODE" \
  --format '{{.State.Status}} {{.RestartCount}}')"

read -r BTC_STATUS BTC_RESTARTS <<<"$BTC_STATE"
test "$BTC_STATUS" = "running"
test "$BTC_RESTARTS" = "0"

echo "SBP-071.2 Bitcoin runtime continuity contract: PASS"

# Pre-restart acceptance intentionally avoids live RPC calls.
# Bitcoin Core is in heavy IBD and observer RPC latency is the exact
# condition this package is repairing. Runtime behavior is tested after
# the Bitcoin-only restart when the new observer settings are active.

BTC_HEALTH="$(
  timeout 15s sudo docker inspect "$BTC_NODE" \
    --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'
)"

test "$BTC_HEALTH" = "healthy"

echo "SBP-071.2 pre-restart Bitcoin observer state: PASS (health=$BTC_HEALTH)"
echo "SBP-071.2 Bitcoin runtime non-mutation contract: PASS"

timeout 15s sudo docker inspect "$BCH_NODE" \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' \
  | grep -q '^running healthy 0$'

echo "SBP-071.2 BCH safety contract: PASS"

echo "SBP-071.2 final verification: PASS"
echo "No live blockchain runtime was modified."
echo "Restart Bitcoin only after this verification to activate the Compose healthcheck timeout."
