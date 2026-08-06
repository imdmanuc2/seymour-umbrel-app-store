#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -d "$BACKUP" ]] || {
  echo "Invalid backup: $BACKUP" >&2
  exit 1
}

rm -rf "$REPO/shared/provider_catalog"
rm -f \
  "$REPO/scripts/seymour-provider-catalog" \
  "$REPO/docs/PROVIDER_CATALOG_INTEGRATION.md" \
  "$REPO/tests/test_provider_catalog.py" \
  "$REPO/tests/test_bch_catalog_compatibility.py"

cp -a "$BACKUP/." "$REPO/"

echo "SBP-007 rollback: PASS"
