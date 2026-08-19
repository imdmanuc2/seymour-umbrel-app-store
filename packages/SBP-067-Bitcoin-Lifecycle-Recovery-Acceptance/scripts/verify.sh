#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
BRIDGE="$REPO/shared/umbrel_control/bridge.py"
START_GUARD="$REPO/shared/blockchain_install/start_guard.py"
RECOVERY="$REPO/shared/blockchain_recovery/engine.py"
HEALTH="$REPO/seymour-blockchain-manager/data/web/runtime_health.py"
REGISTRY="$REPO/seymour-blockchain-manager/data/web/runtime_registry.py"
COMPOSE="$REPO/seymour-bitcoin-node/docker-compose.yml"
HOOK="$REPO/seymour-bitcoin-node/hooks/pre-install"
BTC_APP="seymour-bitcoin-node"
BCH_APP="seymour-bch-node"
echo "SBP-067 verify: Bitcoin lifecycle and recovery acceptance"
grep -q 'storageGuard' "$BRIDGE"
grep -q 'pre-start-verified' "$BRIDGE"
grep -q 'resolve_storage_expectation' "$START_GUARD"
grep -q 'verify_expected_path' "$START_GUARD"
echo "SBP-067 lifecycle storage-guard contract: PASS"
if grep -q '/home/umbrel/umbrel/app-data/seymour-bitcoin-node' "$COMPOSE"; then echo "ERROR: machine-specific Bitcoin path in canonical compose"; exit 1; fi
grep -Fq '${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_RPC_HOST}' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_STATUS_HOST}' "$COMPOSE"
grep -q 'rpc_host="${app_id}-rpc"' "$HOOK"
grep -q 'status_host="${app_id}-status"' "$HOOK"
echo "SBP-067 portable runtime identity contract: PASS"
grep -q 'def docker_compose_container' "$REGISTRY"
grep -q 'com.docker.compose.project' "$REGISTRY"
grep -q 'com.docker.compose.service' "$REGISTRY"
if grep -q '"container": os.environ.get("BTC_NODE_CONTAINER"' "$REGISTRY"; then echo "ERROR: fixed Bitcoin container name returned"; exit 1; fi
echo "SBP-067 provider-neutral discovery contract: PASS"
grep -q 'destructive' "$HEALTH"
grep -q 'recommendedAction\|recommended_action' "$HEALTH"
grep -q 'def plan' "$RECOVERY"
echo "SBP-067 health/recovery guidance contract: PASS"
BTC_NODE="$(sudo docker ps -a --filter "label=com.docker.compose.project=$BTC_APP" --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
BTC_STATUS="$(sudo docker ps -a --filter "label=com.docker.compose.project=$BTC_APP" --filter 'label=com.docker.compose.service=status' --format '{{.Names}}' | head -1)"
BCH_NODE="$(sudo docker ps -a --filter "label=com.docker.compose.project=$BCH_APP" --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
test -n "$BTC_NODE"; test -n "$BTC_STATUS"; test -n "$BCH_NODE"
echo "SBP-067 live runtime discovery contract: PASS"
BTC_STATE="$(sudo docker inspect "$BTC_NODE" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
read -r BTC_STATUS_STATE BTC_HEALTH BTC_RESTARTS <<<"$BTC_STATE"
test "$BTC_STATUS_STATE" = running; test "$BTC_HEALTH" = healthy; test "$BTC_RESTARTS" = 0
echo "SBP-067 live Bitcoin health contract: PASS"
NODE_DATA="$(sudo docker inspect "$BTC_NODE" --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Source}}{{end}}{{end}}')"
STATUS_DATA="$(sudo docker inspect "$BTC_STATUS" --format '{{range .Mounts}}{{if eq .Destination "/node-data"}}{{.Source}}{{end}}{{end}}')"
test -n "$NODE_DATA"; test "$NODE_DATA" = "$STATUS_DATA"
echo "SBP-067 live storage continuity contract: PASS ($NODE_DATA)"
BTC_RPC_HOST="$(sudo docker inspect "$BTC_STATUS" --format '{{range .Config.Env}}{{println .}}{{end}}' | awk -F= '$1=="BTC_RPC_HOST"{print substr($0,index($0,"=")+1)}')"
test -n "$BTC_RPC_HOST"
NODE_ALIASES="$(sudo docker inspect "$BTC_NODE" --format '{{range $n,$v := .NetworkSettings.Networks}}{{printf "%v" $v.Aliases}}{{end}}')"
STATUS_ALIASES="$(sudo docker inspect "$BTC_STATUS" --format '{{range $n,$v := .NetworkSettings.Networks}}{{printf "%v" $v.Aliases}}{{end}}')"
printf '%s\n' "$NODE_ALIASES" | grep -Fq "$BTC_RPC_HOST"
EXPECTED_STATUS="${BTC_APP}-status"
printf '%s\n' "$STATUS_ALIASES" | grep -Fq "$EXPECTED_STATUS"
echo "SBP-067 live runtime identity continuity contract: PASS"
MGR="$(sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-blockchain-manager' --filter 'label=com.docker.compose.service=web' --format '{{.Names}}' | head -1)"
test -n "$MGR"
MGR_JSON="$(sudo docker exec "$MGR" python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8080/api/dashboard",timeout=30).read().decode())')"
python3 - "$MGR_JSON" <<'PYCHECK'
import json,sys
p=json.loads(sys.argv[1]); btc=p.get('providers',{}).get('bitcoin-mainnet',{})
if not btc.get('installed') or not btc.get('running'): raise SystemExit('ERROR: Manager does not report Bitcoin installed/running')
if btc.get('runtimeState') not in {'starting','syncing','running'}: raise SystemExit(f"ERROR: unexpected runtimeState={btc.get('runtimeState')!r}")
rpc=btc.get('rpc') if isinstance(btc.get('rpc'),dict) else {}
if not rpc.get('reachable') or not rpc.get('healthy'): raise SystemExit('ERROR: Manager reports unhealthy Bitcoin RPC')
health=btc.get('health') if isinstance(btc.get('health'),dict) else {}
if bool(health.get('destructive')): raise SystemExit('ERROR: health guidance is destructive')
print(f"SBP-067 Manager lifecycle projection: state={btc.get('runtimeState')} height={btc.get('sync',{}).get('height')} action={health.get('recommendedAction')}")
PYCHECK
echo "SBP-067 Manager health/recovery projection contract: PASS"
BCH_STATE="$(sudo docker inspect "$BCH_NODE" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
read -r BCH_STATUS_STATE BCH_HEALTH BCH_RESTARTS <<<"$BCH_STATE"
test "$BCH_STATUS_STATE" = running; test "$BCH_HEALTH" = healthy; test "$BCH_RESTARTS" = 0
echo "SBP-067 BCH safety contract: PASS"
echo "SBP-067 final Bitcoin lifecycle/recovery acceptance: PASS"
echo "No blockchain runtime was modified."
