#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
COMPOSE="$REPO/seymour-bch-node/docker-compose.yml"
HOOK="$REPO/seymour-bch-node/hooks/pre-install"
INSTALLER="$REPO/seymour-blockchain-manager/data/web/installer.py"
BRIDGE="$REPO/seymour-blockchain-manager/data/shared/umbrel_control/bridge.py"
HTTP_CLIENT="$REPO/seymour-blockchain-manager/data/shared/umbrel_control/http_client.py"

echo "SBP-063.3.9 doctor: checking acceptance prerequisites"
for f in "$COMPOSE" "$HOOK" "$INSTALLER" "$BRIDGE" "$HTTP_CLIENT"; do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done

grep -q 'SEYMOUR_BLOCKCHAIN_LOCAL_DATA_PATH' "$COMPOSE"
grep -q 'SEYMOUR_BLOCKCHAIN_BLOCKS_PATH' "$COMPOSE"
grep -q '/data/blocks' "$COMPOSE"
grep -q '/node-data/blocks' "$COMPOSE"
echo "SBP-063.3.9 hybrid compose prerequisites: PASS"

grep -q 'expected 4 storage anchors' "$HOOK"
echo "SBP-063.3.9 pre-install hook prerequisite: PASS"

grep -q 'InstallStatus.RUNNING' "$INSTALLER"
grep -q 'mutation_timeout_seconds=1800' "$BRIDGE"
grep -q 'mutation_timeout_seconds: float = 1800' "$HTTP_CLIENT"
echo "SBP-063.3.9 install/lifecycle prerequisites: PASS"

echo "SBP-063.3.9 doctor: PASS"
