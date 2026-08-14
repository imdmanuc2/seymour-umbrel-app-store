#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
DOCKERFILE="$ROOT/runtime-images/bitcoin-core/Dockerfile"
WF="$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"

echo "SBP-062.1.1 verify: Bitcoin release prestage build repair"

if grep -qE \
  'curl|bitcoincore\.org|SHA256SUMS' \
  "$DOCKERFILE"
then
  echo "FAIL: Dockerfile still performs release-network work"
  exit 1
fi

grep -q \
  'COPY staged/${TARGETARCH}/bitcoind' \
  "$DOCKERFILE"

grep -q \
  'COPY staged/${TARGETARCH}/bitcoin-cli' \
  "$DOCKERFILE"

grep -q \
  'release_arch: x86_64' \
  "$WF"

grep -q \
  'release_arch: aarch64' \
  "$WF"

grep -q \
  'Download and verify Bitcoin Core release' \
  "$WF"

grep -q \
  -- '--retry 5' \
  "$WF"

grep -q \
  'sha256sum -c SHA256SUMS.selected' \
  "$WF"

grep -q \
  'docker buildx build' \
  "$WF"

grep -q \
  -- '--push' \
  "$WF"

grep -q \
  'imagetools create' \
  "$WF"

echo "SBP-062.1.1 network-free Dockerfile contract: PASS"
echo "SBP-062.1.1 release retry contract: PASS"
echo "SBP-062.1.1 checksum verification contract: PASS"
echo "SBP-062.1.1 direct Buildx push contract: PASS"
echo "SBP-062.1.1 manifest publish contract: PASS"
echo "SBP-062.1.1 final verification: PASS"
echo "No image was published and no live runtime was modified."
