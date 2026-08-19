#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CATALOG="$ROOT/shared/provider_catalog/providers.v1.json"
HOOK="$ROOT/seymour-monero-node/hooks/pre-install"
BINDING="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/evidence/runtime-bindings/seymour-monero-node.env"

echo "SBP-074 verify: Monero persistent storage binding and first-install preflight"

grep -q 'runtime-bindings' "$HOOK"
grep -q 'SEYMOUR_BLOCKCHAIN_DATA_PATH' "$HOOK"
grep -q 'data_path}:/data' "$HOOK"
grep -q 'data_path}:/node-data' "$HOOK"
echo "SBP-074 Monero hook storage materialization contract: PASS"

sudo test -f "$BINDING"

DATA_PATH="$(
  sudo awk -F= '$1=="SEYMOUR_BLOCKCHAIN_DATA_PATH"{print substr($0,index($0,"=")+1)}' "$BINDING"
)"

test -n "$DATA_PATH"
test "${DATA_PATH#/}" != "$DATA_PATH"

PROVIDER="$(
python3 - "$CATALOG" <<'PY'
import json,sys
from pathlib import Path
data=json.loads(Path(sys.argv[1]).read_text())
print(next(p for p in data["providers"] if p["providerId"]=="monero-mainnet")["providerId"])
PY
)"

case "$DATA_PATH" in
  */"$PROVIDER") ;;
  *) echo "ERROR: Monero data path is not provider-derived: $DATA_PATH"; exit 1 ;;
esac

sudo test -d "$DATA_PATH"
TEST="$DATA_PATH/.sbp074-write-test-$$"
touch "$TEST"
rm -f "$TEST"
echo "SBP-074 Monero target write contract: PASS ($DATA_PATH)"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
APP="$TMP/app-data/seymour-monero-node"
MGR="$TMP/app-data/seymour-blockchain-manager/data/evidence/runtime-bindings"
mkdir -p "$APP/hooks" "$MGR"

cp "$ROOT/seymour-monero-node/docker-compose.yml" "$APP/docker-compose.yml"
cp "$HOOK" "$APP/hooks/pre-install"
chmod +x "$APP/hooks/pre-install"
sudo cat "$BINDING" > "$MGR/seymour-monero-node.env"

APP_DATA_DIR="$APP" UMBREL_ROOT="$TMP" "$APP/hooks/pre-install" >/dev/null

grep -Fq "$DATA_PATH:/data" "$APP/docker-compose.yml"
grep -Fq "$DATA_PATH:/node-data" "$APP/docker-compose.yml"
grep -Fq 'seymour-monero-node-rpc' "$APP/docker-compose.yml"
grep -Fq 'seymour-monero-node-status' "$APP/docker-compose.yml"

if grep -q 'SEYMOUR_BLOCKCHAIN_.*HOST' "$APP/docker-compose.yml"; then
  echo "ERROR: unresolved Monero identity remains"; exit 1
fi
echo "SBP-074 isolated Monero materialization contract: PASS"

if timeout 15s sudo docker ps -a --filter 'label=com.docker.compose.project=seymour-monero-node' --format '{{.Names}}' | grep -q .; then
  echo "ERROR: Monero runtime unexpectedly exists"; exit 1
fi
echo "SBP-074 no-live-Monero-runtime contract: PASS"

for APP_ID in seymour-bitcoin-node seymour-bch-node; do
  NODE="$(timeout 15s sudo docker ps -a --filter "label=com.docker.compose.project=$APP_ID" --filter 'label=com.docker.compose.service=node' --format '{{.Names}}' | head -1)"
  test -n "$NODE"
  timeout 15s sudo docker inspect "$NODE" --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} {{.RestartCount}}' | grep -q '^running healthy 0$'
done

echo "SBP-074 BTC/BCH safety contract: PASS"
echo "SBP-074 final first-install storage preflight: PASS"
echo "Monero remains uninstalled."
