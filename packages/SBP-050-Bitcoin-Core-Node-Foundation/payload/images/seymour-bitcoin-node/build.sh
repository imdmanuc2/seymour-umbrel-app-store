#!/usr/bin/env bash
set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/imdmanuc2/seymour-bitcoin-node}"
VERSION="${VERSION:-29.0.0}"
BITCOIN_VERSION="${BITCOIN_VERSION:-29.0}"

docker build \
  --build-arg BITCOIN_VERSION="$BITCOIN_VERSION" \
  -t "${IMAGE}:${VERSION}" \
  "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Built ${IMAGE}:${VERSION}"
