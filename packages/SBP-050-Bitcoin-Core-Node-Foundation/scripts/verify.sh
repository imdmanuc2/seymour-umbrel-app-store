#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"

APP="$ROOT/seymour-bitcoin-node"

echo "SBP-050 verify: installed Bitcoin Core foundation"

[[ -f "$APP/docker-compose.yml" ]]
[[ -f "$APP/umbrel-app.yml" ]]
[[ -x "$APP/data/node/entrypoint.sh" ]]
[[ -f "$APP/data/status/app.py" ]]
[[ -f "$APP/data/contracts/bitcoin-core.json" ]]

python3 -m py_compile "$APP/data/status/app.py"

grep -Fq 'version: "0.2.0"' \
  "$APP/umbrel-app.yml"

grep -Fq 'ghcr.io/imdmanuc2/seymour-bitcoin-node:29.0.0' \
  "$APP/docker-compose.yml"

grep -Fq 'BTC_NETWORK' \
  "$APP/data/node/entrypoint.sh"

grep -Fq '"contract": "seymour.blockchain-runtime"' \
  "$APP/data/contracts/bitcoin-core.json"

grep -Fq '"providerId": "bitcoin-mainnet"' \
  "$APP/data/contracts/bitcoin-core.json"

grep -Fq '"canonicalRuntimeState": true' \
  "$APP/data/contracts/bitcoin-core.json"

if grep -Eq \
  'docker[[:space:]]+(start|stop|restart|rm)|bitcoin-cli[[:space:]].*(stop|setban)' \
  "$APP/data/status/app.py"; then
  echo "SBP-050 verify: prohibited lifecycle mutation found"
  exit 1
fi

echo "SBP-050 installed app contract: PASS"
echo "SBP-050 canonical runtime contract: PASS"
echo "SBP-050 read-only status service: PASS"
echo "SBP-050 final verification: PASS"
echo
echo "No Bitcoin node was started by verify.sh."
