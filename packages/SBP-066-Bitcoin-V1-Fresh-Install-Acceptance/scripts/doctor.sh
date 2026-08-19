#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

WORKFLOW="$REPO/shared/bitcoin_managed_runtime/workflow.py"
RUNTIME_BINDING="$REPO/shared/blockchain_install/runtime_binding.py"
START_GUARD="$REPO/shared/blockchain_install/start_guard.py"
COMPOSE="$REPO/seymour-bitcoin-node/docker-compose.yml"
HOOK="$REPO/seymour-bitcoin-node/hooks/pre-install"
STATUS_APP="$REPO/seymour-bitcoin-node/data/status/app.py"
REGISTRY="$REPO/seymour-blockchain-manager/data/web/runtime_registry.py"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"

echo "SBP-066 doctor: checking Bitcoin V1 acceptance prerequisites"

for f in \
  "$WORKFLOW" "$RUNTIME_BINDING" "$START_GUARD" "$COMPOSE" "$HOOK" \
  "$STATUS_APP" "$REGISTRY" "$CATALOG"
do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done

python3 -m py_compile \
  "$WORKFLOW" \
  "$RUNTIME_BINDING" \
  "$START_GUARD" \
  "$STATUS_APP" \
  "$REGISTRY"

bash -n "$HOOK"

echo "SBP-066 compile/syntax prerequisites: PASS"

grep -q '"bitcoin-mainnet"' "$CATALOG"
grep -q 'INSTALL-seymour-bitcoin-node' "$CATALOG"
echo "SBP-066 provider catalog prerequisite: PASS"

grep -Fq '${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/data' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_DATA_PATH:-${APP_DATA_DIR}/data/node}:/node-data:ro' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_RPC_HOST}' "$COMPOSE"
grep -Fq '${SEYMOUR_BLOCKCHAIN_STATUS_HOST}' "$COMPOSE"
echo "SBP-066 canonical compose prerequisite: PASS"

grep -q 'rpc_host="${app_id}-rpc"' "$HOOK"
grep -q 'status_host="${app_id}-status"' "$HOOK"
echo "SBP-066 derived identity hook prerequisite: PASS"

echo "SBP-066 doctor: PASS"
