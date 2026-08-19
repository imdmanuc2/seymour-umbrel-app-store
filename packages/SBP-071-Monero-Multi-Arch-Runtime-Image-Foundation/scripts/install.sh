#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PKG/scripts/doctor.sh"

mkdir -p \
  "$REPO/.github/workflows" \
  "$REPO/runtime-images/monero"

cp \
  "$PKG/payload/.github/workflows/seymour-monero-node-multiarch.yml" \
  "$REPO/.github/workflows/seymour-monero-node-multiarch.yml"

cp \
  "$PKG/payload/runtime-images/monero/Dockerfile" \
  "$REPO/runtime-images/monero/Dockerfile"

echo "SBP-071 Monero multi-arch workflow installed: PASS"
echo "SBP-071 Monero runtime image context installed: PASS"
echo "No image was built or pushed locally."
echo "Monero remains non-selectable."
echo "No blockchain runtime was modified."
