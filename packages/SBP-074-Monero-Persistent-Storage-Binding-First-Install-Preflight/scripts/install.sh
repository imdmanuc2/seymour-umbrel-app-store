#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STORAGE_ROOT="${SEYMOUR_STORAGE_ROOT:-}"

if [[ -z "$STORAGE_ROOT" ]]; then
  echo "ERROR: set SEYMOUR_STORAGE_ROOT to the selected persistent storage root." >&2
  exit 2
fi

"$PKG/scripts/doctor.sh"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-074-$STAMP"
mkdir -p "$BACKUP"
cp "$ROOT/seymour-monero-node/hooks/pre-install" "$BACKUP/pre-install"

python3 "$PKG/scripts/patch.py" "$ROOT"
bash -n "$ROOT/seymour-monero-node/hooks/pre-install"

cp "$PKG/scripts/seymour-runtime-storage-provision" "$ROOT/scripts/seymour-runtime-storage-provision"
chmod +x "$ROOT/scripts/seymour-runtime-storage-provision"

"$ROOT/scripts/seymour-runtime-storage-provision"   --provider monero-mainnet   --storage-root "$STORAGE_ROOT"   --catalog "$ROOT/shared/provider_catalog/providers.v1.json"

echo "SBP-074 Monero persistent storage preflight: PASS"
echo "Backup: $BACKUP"
echo "Monero was not installed or started."
echo "No existing blockchain runtime was modified."
