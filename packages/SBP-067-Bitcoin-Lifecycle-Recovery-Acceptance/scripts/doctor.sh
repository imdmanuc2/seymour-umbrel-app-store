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
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"
echo "SBP-067 doctor: checking Bitcoin lifecycle/recovery prerequisites"
for f in "$BRIDGE" "$START_GUARD" "$RECOVERY" "$HEALTH" "$REGISTRY" "$COMPOSE" "$HOOK" "$CATALOG"; do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done
python3 -m py_compile "$BRIDGE" "$START_GUARD" "$RECOVERY" "$HEALTH" "$REGISTRY"
bash -n "$HOOK"
echo "SBP-067 compile/syntax prerequisites: PASS"
grep -q '"bitcoin-mainnet"' "$CATALOG"
echo "SBP-067 provider catalog prerequisite: PASS"
echo "SBP-067 doctor: PASS"
