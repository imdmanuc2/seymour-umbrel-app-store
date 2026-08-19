#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TARGET="$REPO/seymour-monero-node"
COMPOSE="$TARGET/docker-compose.yml"
HOOK="$TARGET/hooks/pre-install"
STATUS="$TARGET/data/status/app.py"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"

echo "SBP-070 verify: Monero runtime app foundation"

test -f "$TARGET/umbrel-app.yml"
test -f "$COMPOSE"
test -f "$HOOK"
test -f "$STATUS"

bash -n "$HOOK"
python3 -m py_compile "$STATUS"
echo "SBP-070 canonical source syntax contract: PASS"

grep -Fq '${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data:ro' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_RPC_HOST}' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_STATUS_HOST}' "$COMPOSE"

if grep -q '/home/umbrel/' "$COMPOSE"; then
  echo "ERROR: machine-specific path leaked into canonical Monero compose"
  exit 1
fi

if grep -q 'seymour-monero-node-rpc\|seymour-monero-node-status' "$COMPOSE"; then
  echo "ERROR: generated Monero DNS identity leaked into canonical compose"
  exit 1
fi

echo "SBP-070 portable Monero compose contract: PASS"

grep -q -- '--data-dir=/data' "$COMPOSE"
grep -q -- '--p2p-bind-port=18080' "$COMPOSE"
grep -q -- '--rpc-bind-port=18081' "$COMPOSE"
grep -q -- '--confirm-external-bind' "$COMPOSE"
grep -q -- '--no-igd' "$COMPOSE"
echo "SBP-070 monerod runtime command contract: PASS"

grep -q 'get_info' "$STATUS"
grep -q 'target_height' "$STATUS"
grep -q 'incoming_connections_count' "$STATUS"
grep -q '"providerId": "monero-mainnet"' "$STATUS"
echo "SBP-070 Monero status-service contract: PASS"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
APP_DATA="$TMP/app-data/seymour-monero-node"
mkdir -p "$APP_DATA/hooks"
cp "$COMPOSE" "$APP_DATA/docker-compose.yml"
cp "$HOOK" "$APP_DATA/hooks/pre-install"
chmod +x "$APP_DATA/hooks/pre-install"
APP_DATA_DIR="$APP_DATA" "$APP_DATA/hooks/pre-install" >/dev/null

grep -Fq -- '- seymour-monero-node-rpc' "$APP_DATA/docker-compose.yml"
grep -Fq 'XMR_RPC_HOST: seymour-monero-node-rpc' "$APP_DATA/docker-compose.yml"
grep -Fq 'APP_HOST: seymour-monero-node-status' "$APP_DATA/docker-compose.yml"
grep -Fq -- '- seymour-monero-node-status' "$APP_DATA/docker-compose.yml"
echo "SBP-070 isolated runtime identity materialization: PASS"

python3 - "$CATALOG" <<'PY'
import json
import sys

payload = json.load(open(sys.argv[1]))
xmr = next(
    p for p in payload["providers"]
    if p["providerId"] == "monero-mainnet"
)

assert xmr["availability"] == "planned"
assert xmr["selectable"] is False
assert xmr["productionImage"] is None
assert xmr["runtime"]["appId"] == "seymour-monero-node"

print("SBP-070 Monero non-selectable safety contract: PASS")
PY

if sudo docker ps -a --format '{{.Names}}' | grep -q '^seymour-monero-node'; then
  echo "ERROR: Monero runtime unexpectedly exists in Docker"
  exit 1
fi
echo "SBP-070 no-live-Monero-runtime contract: PASS"

BTC_NODE="$(
  sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bitcoin-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"
BCH_NODE="$(
  sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bch-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"

test -n "$BTC_NODE"
test -n "$BCH_NODE"

sudo docker inspect "$BTC_NODE" \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' \
  | grep -q '^running healthy 0$'

sudo docker inspect "$BCH_NODE" \
  --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' \
  | grep -q '^running healthy 0$'

echo "SBP-070 BTC/BCH safety contract: PASS"
echo "SBP-070 final Monero runtime app foundation: PASS"
echo "No blockchain runtime was modified."
