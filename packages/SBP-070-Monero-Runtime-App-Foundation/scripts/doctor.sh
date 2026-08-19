#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAYLOAD="$PKG/payload/seymour-monero-node"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"

echo "SBP-070 doctor: checking Monero runtime foundation prerequisites"

for f in \
  "$PAYLOAD/umbrel-app.yml" \
  "$PAYLOAD/docker-compose.yml" \
  "$PAYLOAD/hooks/pre-install" \
  "$PAYLOAD/data/status/app.py" \
  "$CATALOG"
do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done

bash -n "$PAYLOAD/hooks/pre-install"
python3 -m py_compile "$PAYLOAD/data/status/app.py"

grep -q '"providerId": "monero-mainnet"' "$CATALOG"
grep -q '"appId": "seymour-monero-node"' "$CATALOG"

echo "SBP-070 Monero provider prerequisite: PASS"
echo "SBP-070 source syntax contract: PASS"
echo "SBP-070 doctor: PASS"
