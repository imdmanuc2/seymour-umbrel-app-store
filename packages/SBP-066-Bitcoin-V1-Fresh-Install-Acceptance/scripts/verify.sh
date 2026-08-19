#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

COMPOSE="$REPO/seymour-bitcoin-node/docker-compose.yml"
HOOK="$REPO/seymour-bitcoin-node/hooks/pre-install"
STATUS_APP="$REPO/seymour-bitcoin-node/data/status/app.py"
REGISTRY="$REPO/seymour-blockchain-manager/data/web/runtime_registry.py"
RUNTIME_BINDING="$REPO/shared/blockchain_install/runtime_binding.py"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"

BTC_APP="seymour-bitcoin-node"
BCH_APP="seymour-bch-node"

echo "SBP-066 verify: Bitcoin V1 fresh-install acceptance"

if grep -q '/home/umbrel/umbrel/app-data/seymour-bitcoin-node' "$COMPOSE"; then
  echo "ERROR: machine-specific Bitcoin data path leaked into canonical compose"
  exit 1
fi

if grep -q 'seymour-bitcoin-node-rpc\|seymour-bitcoin-node-status' "$COMPOSE"; then
  echo "ERROR: runtime-specific Bitcoin DNS identity leaked into canonical compose"
  exit 1
fi

grep -Fq '${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data:ro' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_RPC_HOST}' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_STATUS_HOST}' "$COMPOSE"
echo "SBP-066 provider-neutral canonical compose contract: PASS"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

APP_DATA="$TMP/app-data/$BTC_APP"
mkdir -p \
  "$APP_DATA/hooks" \
  "$APP_DATA/data/node" \
  "$APP_DATA/data/generated" \
  "$APP_DATA/data/state" \
  "$APP_DATA/data/status" \
  "$APP_DATA/data/contracts"

cp "$COMPOSE" "$APP_DATA/docker-compose.yml"
cp "$HOOK" "$APP_DATA/hooks/pre-install"
chmod +x "$APP_DATA/hooks/pre-install"

APP_DATA_DIR="$APP_DATA" "$APP_DATA/hooks/pre-install" >/dev/null

EXPECTED_RPC="${BTC_APP}-rpc"
EXPECTED_STATUS="${BTC_APP}-status"

grep -Fq -- "- $EXPECTED_RPC" "$APP_DATA/docker-compose.yml"
grep -Fq "BTC_RPC_HOST: $EXPECTED_RPC" "$APP_DATA/docker-compose.yml"
grep -Fq -- "- $EXPECTED_STATUS" "$APP_DATA/docker-compose.yml"

if grep -Fq '${SEYMOUR_BLOCKCHAIN_RPC_HOST}' "$APP_DATA/docker-compose.yml"; then
  echo "ERROR: isolated compose retains unresolved RPC host"
  exit 1
fi
if grep -Fq '${SEYMOUR_BLOCKCHAIN_STATUS_HOST}' "$APP_DATA/docker-compose.yml"; then
  echo "ERROR: isolated compose retains unresolved status host"
  exit 1
fi
echo "SBP-066 isolated DNS identity materialization contract: PASS"

STAGED_DATA="$TMP/runtime-data/$BTC_APP"
mkdir -p "$STAGED_DATA"

python3 - "$RUNTIME_BINDING" "$APP_DATA/docker-compose.yml" "$STAGED_DATA" <<'PY'
from pathlib import Path
import importlib.util
import sys

module_path = Path(sys.argv[1])
compose = Path(sys.argv[2])
data_path = Path(sys.argv[3]).resolve()

spec = importlib.util.spec_from_file_location("sbp066_runtime_binding", module_path)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = module
spec.loader.exec_module(module)

plan = module.persist_runtime_binding(
    provider_id="bitcoin-mainnet",
    app_id="seymour-bitcoin-node",
    compose_path=compose,
    data_path=data_path,
)

assert plan.provider_id == "bitcoin-mainnet"
assert plan.app_id == "seymour-bitcoin-node"
assert plan.data_path == data_path
PY

grep -Fq "$STAGED_DATA:/data" "$APP_DATA/docker-compose.yml"
grep -Fq "$STAGED_DATA:/node-data" "$APP_DATA/docker-compose.yml"

if grep -Eq 'SEYMOUR_BLOCKCHAIN_DATA_PATH[^[:space:]]*:/data([[:space:]]|$)' "$APP_DATA/docker-compose.yml"; then
  echo "ERROR: staged /data storage variable remains unresolved"
  exit 1
fi
if grep -Eq 'SEYMOUR_BLOCKCHAIN_DATA_PATH[^[:space:]]*:/node-data' "$APP_DATA/docker-compose.yml"; then
  echo "ERROR: staged /node-data storage variable remains unresolved"
  exit 1
fi
echo "SBP-066 isolated storage-binding persistence contract: PASS"

grep -q 'def docker_compose_container' "$REGISTRY"
grep -q 'com.docker.compose.project' "$REGISTRY"
grep -q 'com.docker.compose.service' "$REGISTRY"

if grep -q '"container": os.environ.get("BTC_NODE_CONTAINER"' "$REGISTRY"; then
  echo "ERROR: fixed Bitcoin container identity remains in Manager registry"
  exit 1
fi
if grep -q 'docker_container(runtime\["container"\])' "$REGISTRY"; then
  echo "ERROR: legacy fixed-name Bitcoin runtime discovery remains"
  exit 1
fi
echo "SBP-066 provider-neutral runtime discovery contract: PASS"

grep -q 'getblockchaininfo' "$STATUS_APP"
grep -q 'getnetworkinfo' "$STATUS_APP"
grep -q 'uptime' "$STATUS_APP"
grep -q 'telemetryStale' "$STATUS_APP"
grep -q 'live-cache' "$STATUS_APP"
echo "SBP-066 resilient Bitcoin telemetry source contract: PASS"

BTC_NODE="$(
  sudo docker ps -a \
    --filter "label=com.docker.compose.project=$BTC_APP" \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' \
    | head -1
)"

BTC_STATUS="$(
  sudo docker ps -a \
    --filter "label=com.docker.compose.project=$BTC_APP" \
    --filter 'label=com.docker.compose.service=status' \
    --format '{{.Names}}' \
    | head -1
)"

BCH_NODE="$(
  sudo docker ps -a \
    --filter "label=com.docker.compose.project=$BCH_APP" \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' \
    | head -1
)"

test -n "$BTC_NODE"
test -n "$BTC_STATUS"
test -n "$BCH_NODE"
echo "SBP-066 live Compose-label discovery contract: PASS"

BTC_STATE="$(sudo docker inspect "$BTC_NODE" \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
read -r BTC_STATUS_STATE BTC_HEALTH BTC_RESTARTS <<<"$BTC_STATE"
test "$BTC_STATUS_STATE" = "running"
test "$BTC_HEALTH" = "healthy"
test "$BTC_RESTARTS" = "0"
echo "SBP-066 live Bitcoin health contract: PASS"

BTC_STATUS_JSON="$(
  sudo docker exec "$BTC_STATUS" \
    python -c '
import urllib.request
print(
    urllib.request.urlopen(
        "http://127.0.0.1:8080/api/status",
        timeout=15
    ).read().decode()
)
'
)"

python3 - "$BTC_STATUS_JSON" <<'PY'
import json
import sys

p = json.loads(sys.argv[1])

if p.get("chain") != "bitcoin":
    raise SystemExit(f"ERROR: unexpected Bitcoin status chain: {p.get('chain')!r}")

if not p.get("runtimeRpcReachable"):
    raise SystemExit("ERROR: Bitcoin status RPC is not reachable")

if not p.get("runtimeRpcHealthy"):
    raise SystemExit("ERROR: Bitcoin status RPC is not healthy")

subversion = str(p.get("subversion") or "")
if not subversion.startswith("/Satoshi:"):
    raise SystemExit(
        f"ERROR: Bitcoin status is not reporting Bitcoin Core: {subversion!r}"
    )
if "Bitcoin Cash" in subversion:
    raise SystemExit(
        f"ERROR: Bitcoin status crossed into BCH telemetry: {subversion!r}"
    )

blocks = p.get("blocks")
headers = p.get("headers")

if not isinstance(blocks, int) or blocks < 1:
    raise SystemExit(f"ERROR: invalid Bitcoin block height: {blocks!r}")
if not isinstance(headers, int) or headers < blocks:
    raise SystemExit(
        f"ERROR: invalid Bitcoin header height: blocks={blocks!r} headers={headers!r}"
    )

print(
    "SBP-066 Bitcoin status telemetry: "
    f"blocks={blocks} headers={headers} subversion={subversion}"
)
PY

echo "SBP-066 live Bitcoin chain-identity telemetry contract: PASS"

MGR="$(
  sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-blockchain-manager' \
    --filter 'label=com.docker.compose.service=web' \
    --format '{{.Names}}' \
    | head -1
)"
test -n "$MGR"

MGR_JSON="$(
  sudo docker exec "$MGR" \
    python -c '
import urllib.request
print(
    urllib.request.urlopen(
        "http://127.0.0.1:8080/api/dashboard",
        timeout=30
    ).read().decode()
)
'
)"

python3 - "$MGR_JSON" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
btc = payload.get("providers", {}).get("bitcoin-mainnet", {})

if not btc.get("installed"):
    raise SystemExit("ERROR: Blockchain Manager reports Bitcoin not installed")
if not btc.get("running"):
    raise SystemExit("ERROR: Blockchain Manager reports Bitcoin not running")
if btc.get("runtimeState") not in {"starting", "syncing", "running"}:
    raise SystemExit(
        f"ERROR: unexpected Bitcoin runtime state: {btc.get('runtimeState')!r}"
    )

rpc = btc.get("rpc") if isinstance(btc.get("rpc"), dict) else {}
if not rpc.get("reachable"):
    raise SystemExit("ERROR: Blockchain Manager reports Bitcoin RPC unreachable")

subversion = str(btc.get("subversion") or "")
if subversion and not subversion.startswith("/Satoshi:"):
    raise SystemExit(
        f"ERROR: Manager Bitcoin provider reports unexpected subversion: {subversion!r}"
    )

print(
    "SBP-066 Manager Bitcoin projection: "
    f"state={btc.get('runtimeState')} "
    f"height={btc.get('sync', {}).get('height')} "
    f"subversion={subversion or 'initializing'}"
)
PY

echo "SBP-066 Blockchain Manager projection contract: PASS"

BCH_STATE="$(sudo docker inspect "$BCH_NODE" \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
read -r BCH_STATUS_STATE BCH_HEALTH BCH_RESTARTS <<<"$BCH_STATE"
test "$BCH_STATUS_STATE" = "running"
test "$BCH_HEALTH" = "healthy"
test "$BCH_RESTARTS" = "0"
echo "SBP-066 BCH safety contract: PASS"

echo "SBP-066 final Bitcoin V1 fresh-install acceptance: PASS"
echo "No blockchain runtime was modified."
