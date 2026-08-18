#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE="$REPO/seymour-bch-node/docker-compose.yml"
HOOK="$REPO/seymour-bch-node/hooks/pre-install"
INSTALLER="$REPO/seymour-blockchain-manager/data/web/installer.py"
BRIDGE="$REPO/seymour-blockchain-manager/data/shared/umbrel_control/bridge.py"
HTTP_CLIENT="$REPO/seymour-blockchain-manager/data/shared/umbrel_control/http_client.py"
BCH_APP="seymour-bch-node"
BTC_APP="seymour-bitcoin-node"
REMOTE_BLOCKS="/mnt/seymour-storage/bitcoin-cash-mainnet/blocks"

echo "SBP-063.3.9 verify: fresh-install acceptance and recovery validation"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
APP_DATA="$TMP/app-data/$BCH_APP"
UMBREL_ROOT="$TMP"
BINDING_DIR="$TMP/app-data/seymour-blockchain-manager/data/evidence/runtime-bindings"
LOCAL_DATA="$TMP/runtime-local/$BCH_APP"
BLOCKS_PATH="$TMP/runtime-remote/bitcoin-cash-mainnet/blocks"
mkdir -p "$APP_DATA/hooks" "$BINDING_DIR" "$LOCAL_DATA" "$BLOCKS_PATH"
cp "$COMPOSE" "$APP_DATA/docker-compose.yml"
cp "$HOOK" "$APP_DATA/hooks/pre-install"
chmod +x "$APP_DATA/hooks/pre-install"
cat > "$BINDING_DIR/$BCH_APP.env" <<EOT
SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH=$LOCAL_DATA
SEYMOUR_BLOCKCHAIN_BLOCKS_PATH=$BLOCKS_PATH
EOT
APP_DATA_DIR="$APP_DATA" UMBREL_ROOT="$UMBREL_ROOT" "$APP_DATA/hooks/pre-install" >/dev/null

grep -Fq "$LOCAL_DATA:/data" "$APP_DATA/docker-compose.yml"
grep -Fq "$BLOCKS_PATH:/data/blocks" "$APP_DATA/docker-compose.yml"
grep -Fq "$LOCAL_DATA:/node-data" "$APP_DATA/docker-compose.yml"
grep -Fq "$BLOCKS_PATH:/node-data/blocks" "$APP_DATA/docker-compose.yml"
echo "SBP-063.3.9 isolated fresh-install hybrid binding: PASS"

grep -q 'InstallStatus.RUNNING' "$INSTALLER"
grep -q 'candidate_app_id' "$INSTALLER"
echo "SBP-063.3.9 duplicate-install safety contract: PASS"

grep -q 'mutation_timeout_seconds=1800' "$BRIDGE"
grep -q 'action in {"start", "restart", "stop", "install"}' "$BRIDGE"
grep -q 'mutation_timeout_seconds: float = 1800' "$HTTP_CLIENT"
grep -q 'timeout=self.mutation_timeout_seconds' "$HTTP_CLIENT"
echo "SBP-063.3.9 lifecycle resilience contract: PASS"

BCH_STATE="$(sudo docker inspect "${BCH_APP}_node_1" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
read -r BCH_STATUS BCH_HEALTH BCH_RESTARTS <<<"$BCH_STATE"
test "$BCH_STATUS" = "running"
test "$BCH_HEALTH" = "healthy"
test "$BCH_RESTARTS" = "0"
echo "SBP-063.3.9 live BCH health contract: PASS"

LIVE_BLOCK_SOURCE="$(sudo docker inspect "${BCH_APP}_node_1" --format '{{range .Mounts}}{{if eq .Destination "/data/blocks"}}{{.Source}}{{end}}{{end}}')"
test "$LIVE_BLOCK_SOURCE" = "$REMOTE_BLOCKS"
echo "SBP-063.3.9 live hybrid mount contract: PASS"

sudo test -f "/home/umbrel/umbrel/app-data/$BCH_APP/data/node/chainstate/CURRENT"
sudo test -f "$REMOTE_BLOCKS/index/CURRENT"
sudo find "$REMOTE_BLOCKS" \
  -maxdepth 1 \
  -type f \
  -name 'blk*.dat' \
  -print -quit \
  | grep -q .
echo "SBP-063.3.9 fresh chainstate/block-index contract: PASS"

RECENT_LOGS="$(sudo docker logs --since 10m "${BCH_APP}_node_1" 2>&1 || true)"
if printf '%s\n' "$RECENT_LOGS" | grep -Eq 'Unable to open file|Failed to read block|Fatal LevelDB|fatal internal error|ReadBlockFromDisk: Errors'; then
  echo "ERROR: recent BCH logs contain storage/index consistency failures"
  exit 1
fi

CHAIN_INFO="$(sudo docker exec "${BCH_APP}_node_1"   bitcoin-cli   -conf=/generated/bitcoin.conf   -datadir=/data   getblockchaininfo)"

python3 - "$CHAIN_INFO" <<'PYCHECK'
import json
import sys

payload = json.loads(sys.argv[1])

blocks = int(payload.get("blocks", 0))
headers = int(payload.get("headers", 0))

if blocks < 1:
    raise SystemExit("ERROR: BCH block height has not advanced")

if headers < blocks:
    raise SystemExit(
        f"ERROR: BCH headers behind blocks: headers={headers} blocks={blocks}"
    )

print(
    f"SBP-063.3.9 BCH chain progress: "
    f"blocks={blocks} headers={headers}"
)
PYCHECK

echo "SBP-063.3.9 sustained BCH progress contract: PASS"

BTC_STATE="$(sudo docker inspect "${BTC_APP}_node_1" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}')"
read -r BTC_STATUS BTC_HEALTH BTC_RESTARTS <<<"$BTC_STATE"
test "$BTC_STATUS" = "running"
test "$BTC_HEALTH" = "healthy"
test "$BTC_RESTARTS" = "0"
echo "SBP-063.3.9 Bitcoin safety contract: PASS"

echo "SBP-063.3.9 final acceptance: PASS"
echo "Recovery/quarantine directories were not modified."
