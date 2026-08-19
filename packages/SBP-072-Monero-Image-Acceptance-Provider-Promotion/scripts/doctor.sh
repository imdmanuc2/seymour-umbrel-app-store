#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "SBP-072 doctor: checking Monero image acceptance prerequisites"
for f in \
 "$REPO/shared/provider_catalog/providers.v1.json" \
 "$REPO/seymour-monero-node/docker-compose.yml" \
 "$REPO/.github/workflows/seymour-monero-node-multiarch.yml" \
 "$REPO/runtime-images/monero/Dockerfile"
do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done
python3 -m py_compile "$PKG/scripts/patch.py"
grep -q '"providerId": "monero-mainnet"' "$REPO/shared/provider_catalog/providers.v1.json"
grep -Fq 'ghcr.io/imdmanuc2/seymour-monero-node:0.18.5.1' "$REPO/seymour-monero-node/docker-compose.yml"
echo "SBP-072 doctor: PASS"
