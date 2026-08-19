#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
TARGET="$REPO/seymour-monero-node"

if [[ -d "$TARGET" ]]; then
  rm -rf "$TARGET"
fi

echo "SBP-070 rollback: canonical Monero source removed."
echo "No blockchain runtime was modified."
