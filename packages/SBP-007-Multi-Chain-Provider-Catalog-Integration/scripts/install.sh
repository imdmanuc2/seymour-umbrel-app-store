#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-007-$STAMP"

"$ROOT/scripts/doctor.sh" "$REPO"

mkdir -p "$BACKUP"

for path in \
  shared/provider_catalog \
  scripts/seymour-provider-catalog \
  docs/PROVIDER_CATALOG_INTEGRATION.md \
  tests/test_provider_catalog.py \
  tests/test_bch_catalog_compatibility.py; do
  if [[ -e "$REPO/$path" ]]; then
    mkdir -p "$BACKUP/$(dirname "$path")"
    cp -a "$REPO/$path" "$BACKUP/$path"
  fi
done

mkdir -p \
  "$REPO/shared/provider_catalog" \
  "$REPO/docs" \
  "$REPO/tests"

cp -a "$ROOT/payload/shared/provider_catalog/." \
  "$REPO/shared/provider_catalog/"

cp "$ROOT/payload/scripts/seymour-provider-catalog" \
  "$REPO/scripts/seymour-provider-catalog"

cp "$ROOT/payload/docs/PROVIDER_CATALOG_INTEGRATION.md" \
  "$REPO/docs/PROVIDER_CATALOG_INTEGRATION.md"

cp "$ROOT/payload/tests/test_provider_catalog.py" \
  "$REPO/tests/test_provider_catalog.py"

cp "$ROOT/payload/tests/test_bch_catalog_compatibility.py" \
  "$REPO/tests/test_bch_catalog_compatibility.py"

chmod +x "$REPO/scripts/seymour-provider-catalog"

echo "Backup: $BACKUP"
echo "SBP-007 install: PASS"
echo "No live Umbrel app was changed."
echo "No container image was published."
