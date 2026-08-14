#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

"$PKG/scripts/doctor.sh" "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-062.1.1-prestage-$STAMP"

mkdir -p "$BACKUP"

cp -a \
  "$ROOT/runtime-images/bitcoin-core/Dockerfile" \
  "$BACKUP/Dockerfile"

cp -a \
  "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml" \
  "$BACKUP/seymour-bitcoin-node-multiarch.yml"

cp \
  "$PKG/payload/runtime-images/bitcoin-core/Dockerfile" \
  "$ROOT/runtime-images/bitcoin-core/Dockerfile"

cp \
  "$PKG/payload/.github/workflows/seymour-bitcoin-node-multiarch.yml" \
  "$ROOT/.github/workflows/seymour-bitcoin-node-multiarch.yml"

rm -rf \
  "$ROOT/runtime-images/bitcoin-core/staged"

echo "Backup: $BACKUP"
echo "SBP-062.1.1 release prestage Dockerfile installed: PASS"
echo "SBP-062.1.1 explicit release download/checksum workflow installed: PASS"
echo "SBP-062.1.1 install: PASS"
echo "No image was published and no live runtime was modified."
