#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LIVE="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data"
echo "SBP-064 verify: blockchain runtime health and recovery guidance"
python3 -m py_compile "$REPO/seymour-blockchain-manager/data/web/runtime_health.py" "$REPO/seymour-blockchain-manager/data/web/telemetry.py" "$LIVE/web/runtime_health.py" "$LIVE/web/telemetry.py"
echo "SBP-064 Python compile contract: PASS"
grep -q 'def runtime_health' "$REPO/seymour-blockchain-manager/data/web/runtime_health.py"
grep -q 'reasonCode' "$REPO/seymour-blockchain-manager/data/web/runtime_health.py"
grep -q 'recommendedAction' "$REPO/seymour-blockchain-manager/data/web/runtime_health.py"
echo "SBP-064 provider-neutral health contract: PASS"
grep -q '"health": health' "$REPO/seymour-blockchain-manager/data/web/telemetry.py"
grep -q 'runtimeHealthGuidance' "$REPO/seymour-blockchain-manager/data/web/app.js"
grep -q 'runtime-guidance-card' "$REPO/seymour-blockchain-manager/data/web/app.js"
grep -q 'ops-health-guidance' "$REPO/seymour-blockchain-manager/data/web/app.js"
echo "SBP-064 projection/UI contracts: PASS"
python3 - "$REPO/seymour-blockchain-manager/data/web" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from runtime_health import runtime_health
cases = [
    (runtime_health(runtime_state='running', rpc_reachable=True, rpc_healthy=True, sync={'initialBlockDownload': False}), 'healthy', 'runtime-healthy'),
    (runtime_health(runtime_state='syncing', rpc_reachable=True, rpc_healthy=True, sync={'initialBlockDownload': True}), 'healthy', 'syncing'),
    (runtime_health(runtime_state='running', rpc_reachable=False, rpc_healthy=False), 'critical', 'rpc-unreachable'),
    (runtime_health(runtime_state='running', rpc_reachable=True, rpc_healthy=True, storage={'healthy': False, 'error': 'storage-binding-mismatch'}), 'critical', 'storage-unhealthy'),
]
for payload, state, reason in cases:
    assert payload['state'] == state, payload
    assert payload['reasonCode'] == reason, payload
    assert payload['destructive'] is False, payload
print('SBP-064 isolated health projection regression: PASS')
PY
repo_sum="$(sha256sum "$REPO/seymour-blockchain-manager/data/web/runtime_health.py" "$REPO/seymour-blockchain-manager/data/web/telemetry.py" "$REPO/seymour-blockchain-manager/data/web/app.js" | awk '{print $1}' | tr '\n' ' ')"
live_sum="$(sha256sum "$LIVE/web/runtime_health.py" "$LIVE/web/telemetry.py" "$LIVE/web/app.js" | awk '{print $1}' | tr '\n' ' ')"
test "$repo_sum" = "$live_sum"
echo "SBP-064 deployed checksum contract: PASS"
BCH="$(sudo docker inspect seymour-bch-node_node_1 --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
BTC="$(sudo docker inspect seymour-bitcoin-node_node_1 --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
read -r bs bh br <<<"$BCH"; read -r ts th tr <<<"$BTC"
test "$bs" = running; test "$bh" = healthy; test "$br" = 0
test "$ts" = running; test "$th" = healthy; test "$tr" = 0
echo "SBP-064 blockchain runtime safety contract: PASS"
echo "SBP-064 final verification: PASS"
echo "No live blockchain runtime was modified."
