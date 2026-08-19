#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

WF="$PKG/payload/.github/workflows/seymour-monero-node-multiarch.yml"
DOCKERFILE="$PKG/payload/runtime-images/monero/Dockerfile"
CATALOG="$REPO/shared/provider_catalog/providers.v1.json"
COMPOSE="$REPO/seymour-monero-node/docker-compose.yml"

echo "SBP-071 doctor: checking Monero multi-arch image prerequisites"

for f in "$WF" "$DOCKERFILE" "$CATALOG" "$COMPOSE"; do
  test -f "$f" || { echo "ERROR: missing $f"; exit 1; }
done

grep -q '0.18.5.1' "$WF"
grep -q 'linux/amd64' "$WF"
grep -q 'linux/arm64' "$WF"
grep -q 'monero-linux-x64-v0.18.5.1.tar.bz2' "$WF"
grep -q 'monero-linux-armv8-v0.18.5.1.tar.bz2' "$WF"

echo "SBP-071 release workflow prerequisite: PASS"
echo "SBP-071 doctor: PASS"
