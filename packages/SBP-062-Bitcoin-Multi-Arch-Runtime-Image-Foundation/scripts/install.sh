#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-062-$STAMP"

mkdir -p \
  "$BACKUP" \
  "$ROOT/runtime-images/bitcoin-core" \
  "$ROOT/.github/workflows"

if [ -d "$ROOT/runtime-images/bitcoin-core" ]; then
  cp -a "$ROOT/runtime-images/bitcoin-core" "$BACKUP/bitcoin-core" 2>/dev/null || true
fi

if [ -f "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml" ]; then
  cp -a \
    "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml" \
    "$BACKUP/seymour-bitcoin-node-multiarch.yml"
fi

cp -a \
  "$PKG/payload/runtime-images/bitcoin-core/." \
  "$ROOT/runtime-images/bitcoin-core/"

cp \
  "$PKG/payload/.github/workflows/seymour-bitcoin-node-multiarch.yml" \
  "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"

echo "Backup: $BACKUP"
echo "SBP-062 Bitcoin multi-arch build context installed: PASS"
echo "SBP-062 GHCR Buildx workflow installed: PASS"
echo "SBP-062 install: PASS"
echo "No image was published."
echo "No blockchain runtime was restarted and no blockchain data was modified."
