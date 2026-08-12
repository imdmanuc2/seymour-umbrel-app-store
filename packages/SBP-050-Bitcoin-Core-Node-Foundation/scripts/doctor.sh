#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

APP="$PKG/payload/seymour-bitcoin-node"
IMAGE="$PKG/payload/images/seymour-bitcoin-node"

echo "SBP-050 doctor: checking Bitcoin Core foundation"

command -v python3 >/dev/null
command -v docker >/dev/null

[[ -f "$APP/docker-compose.yml" ]]
[[ -f "$APP/umbrel-app.yml" ]]
[[ -f "$APP/data/node/entrypoint.sh" ]]
[[ -f "$APP/data/status/app.py" ]]
[[ -f "$APP/data/contracts/bitcoin-core.json" ]]
[[ -f "$IMAGE/Dockerfile" ]]
[[ -f "$IMAGE/build.sh" ]]

grep -Fq 'ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0' \
  "$APP/docker-compose.yml"

grep -Fq 'BTC_NETWORK' \
  "$APP/data/node/entrypoint.sh"

grep -Fq 'runtimeState' \
  "$APP/data/status/app.py"

grep -Fq '"providerId": "bitcoin-mainnet"' \
  "$APP/data/contracts/bitcoin-core.json"

python3 -m py_compile "$APP/data/status/app.py"

echo "SBP-050 doctor: Bitcoin Core runtime anchors PASS"
echo "SBP-050 doctor: canonical status contract PASS"
echo "SBP-050 doctor: PASS"
