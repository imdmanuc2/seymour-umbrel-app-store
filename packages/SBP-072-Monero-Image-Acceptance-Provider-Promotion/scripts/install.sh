#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-072-$STAMP"
"$PKG/scripts/doctor.sh"
mkdir -p "$BACKUP"
for rel in \
 shared/provider_catalog/providers.v1.json \
 seymour-blockchain-manager/data/catalog/providers.v1.json \
 seymour-blockchain-manager/data/shared/provider_catalog/providers.v1.json
do
  mkdir -p "$BACKUP/$(dirname "$rel")"
  cp "$REPO/$rel" "$BACKUP/$rel"
done
python3 "$PKG/scripts/patch.py" "$REPO"
echo "SBP-072 catalog promotion: PASS"
echo "Backup: $BACKUP"
echo "Monero remains non-selectable."
echo "No blockchain runtime was modified."
