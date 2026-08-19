#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

INSTALLER="$ROOT/seymour-blockchain-manager/data/web/installer.py"
CATALOG="$ROOT/shared/provider_catalog/providers.v1.json"
COMPOSE="$ROOT/seymour-monero-node/docker-compose.yml"
HOOK="$ROOT/seymour-monero-node/hooks/pre-install"
IMAGE="ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1"

echo "SBP-073 doctor: checking Monero installation adapter prerequisites"

test -f "$INSTALLER"
test -f "$CATALOG"
test -f "$COMPOSE"
test -f "$HOOK"

python3 -m py_compile "$INSTALLER"

python3 - "$CATALOG" <<'PY'
import json
import sys
from pathlib import Path

catalog = json.loads(Path(sys.argv[1]).read_text())

provider = next(
    p for p in catalog["providers"]
    if p["providerId"] == "monero-mainnet"
)

assert provider["productionImage"] == \
    "ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1"

assert provider["runtime"]["appId"] == "seymour-monero-node"
assert provider["runtime"]["rpc"]["port"] == 18081
assert provider["runtime"]["rpc"]["authentication"] == "none"
assert provider["runtime"]["p2p"]["port"] == 18080
PY

grep -q 'SEYMOUR_BLOCKCHAIN_DATA_PATH' "$COMPOSE"
grep -q 'SEYMOUR_BLOCKCHAIN_RPC_HOST' "$COMPOSE"
grep -q 'SEYMOUR_BLOCKCHAIN_STATUS_HOST' "$COMPOSE"

grep -q 'rpc_host="${app_id}-rpc"' "$HOOK"
grep -q 'status_host="${app_id}-status"' "$HOOK"

echo "SBP-073 Monero prerequisites: PASS"
echo "SBP-073 doctor: PASS"
