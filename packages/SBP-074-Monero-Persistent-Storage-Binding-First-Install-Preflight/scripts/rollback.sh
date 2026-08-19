#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
LATEST="$(find "$ROOT/backups" -maxdepth 1 -type d -name 'sbp-074-*' | sort | tail -1)"
test -n "$LATEST" || { echo "ERROR: no SBP-074 backup found"; exit 1; }
cp "$LATEST/pre-install" "$ROOT/seymour-monero-node/hooks/pre-install"
rm -f "$ROOT/scripts/seymour-runtime-storage-provision"
echo "SBP-074 rollback restored source files."
echo "Provisioned storage and binding evidence are intentionally retained."
echo "No blockchain runtime was modified."
