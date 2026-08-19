#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

rm -f \
  "$REPO/.github/workflows/seymour-monero-node-multiarch.yml"

rm -rf \
  "$REPO/runtime-images/monero"

echo "SBP-071 rollback: source build foundation removed."
echo "Published registry images, if any, are intentionally not deleted."
echo "No blockchain runtime was modified."
