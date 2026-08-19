#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

INSTALLER="$ROOT/seymour-blockchain-manager/data/web/installer.py"
CATALOG="$ROOT/shared/provider_catalog/providers.v1.json"
ADAPTER="$ROOT/scripts/seymour-install-monero"

echo "SBP-073 verify: guarded Monero installation adapter"

python3 -m py_compile "$INSTALLER"

grep -q '"monero-mainnet": {' "$INSTALLER"
grep -q '/control/seymour-install-monero' "$INSTALLER"
grep -q '"rpcPrefix": "XMR"' "$INSTALLER"

echo "SBP-073 installer adapter contract: PASS"

python3 - "$CATALOG" <<'PY'
import json
import sys
from pathlib import Path

catalog = json.loads(Path(sys.argv[1]).read_text())

provider = next(
    p for p in catalog["providers"]
    if p["providerId"] == "monero-mainnet"
)

assert provider["availability"] == "available"
assert provider["selectable"] is True
assert provider["runtime"]["appId"] == "seymour-monero-node"
assert provider["runtime"]["rpc"]["authentication"] == "none"
assert provider["runtime"]["rpc"]["port"] == 18081
assert provider["runtime"]["p2p"]["port"] == 18080
PY

echo "SBP-073 provider selectable contract: PASS"

test -x "$ADAPTER"

OUTPUT="$("$ADAPTER")"

echo "$OUTPUT" | grep -q '"executed": false'
echo "$OUTPUT" | grep -q 'INSTALL-seymour-monero-node'

echo "SBP-073 dry-run/confirmation contract: PASS"

set +e
"$ADAPTER" \
  --execute \
  --confirm WRONG-TOKEN \
  >/tmp/sbp073-wrong.out \
  2>/tmp/sbp073-wrong.err
RC=$?
set -e

test "$RC" -ne 0
grep -q 'Confirmation mismatch' /tmp/sbp073-wrong.err

rm -f \
  /tmp/sbp073-wrong.out \
  /tmp/sbp073-wrong.err

echo "SBP-073 wrong-token prohibition contract: PASS"

MONERO="$(
  timeout 15s sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-monero-node' \
    --format '{{.Names}}' \
    | head -1
)"

test -z "$MONERO"

echo "SBP-073 no-live-Monero-runtime contract: PASS"

BTC="$(
  timeout 15s sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bitcoin-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"

BCH="$(
  timeout 15s sudo docker ps -a \
    --filter 'label=com.docker.compose.project=seymour-bch-node' \
    --filter 'label=com.docker.compose.service=node' \
    --format '{{.Names}}' | head -1
)"

test -n "$BTC"
test -n "$BCH"

BTC_STATE="$(
  timeout 15s sudo docker inspect "$BTC" \
    --format '{{.State.Status}} {{.RestartCount}}'
)"

BCH_STATE="$(
  timeout 15s sudo docker inspect "$BCH" \
    --format '{{.State.Status}} {{.RestartCount}}'
)"

grep -q '^running 0$' <<<"$BTC_STATE"
grep -q '^running 0$' <<<"$BCH_STATE"

echo "SBP-073 BTC/BCH safety contract: PASS"

echo "SBP-073 final verification: PASS"
echo "Monero is selectable but remains uninstalled."
echo "No blockchain runtime was modified."
