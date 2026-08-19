#!/usr/bin/env bash
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LATEST="$(find "$REPO/backups" -maxdepth 1 -type d -name 'sbp-072-*' | sort | tail -1)"
test -n "$LATEST" || { echo "ERROR: no SBP-072 backup found"; exit 1; }
for rel in \
 shared/provider_catalog/providers.v1.json \
 seymour-blockchain-manager/data/catalog/providers.v1.json \
 seymour-blockchain-manager/data/shared/provider_catalog/providers.v1.json
do
  cp "$LATEST/$rel" "$REPO/$rel"
done
echo "SBP-072 rollback: PASS"
echo "No blockchain runtime was modified."
