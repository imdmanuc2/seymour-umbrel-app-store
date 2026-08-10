#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
POINTER="$ROOT/backups/sbp-035-latest"
[[ -f "$POINTER" ]] || { echo "SBP-035 rollback: no backup pointer found" >&2; exit 1; }
BACKUP="$(cat "$POINTER")"
[[ -d "$BACKUP" ]] || { echo "SBP-035 rollback: backup directory missing: $BACKUP" >&2; exit 1; }
for rel in \
  shared/app_lifecycle/__init__.py \
  shared/app_lifecycle/projection.py \
  shared/app_lifecycle/api.py \
  shared/contracts/app-lifecycle-result-v1.json \
  shared/contracts/app-lifecycle-api-v1.json \
  tests/test_sbp035_api.py \
  tests/test_sbp035_contract.py; do
  if [[ -e "$BACKUP/$rel" ]]; then
    mkdir -p "$ROOT/$(dirname "$rel")"
    cp -a "$BACKUP/$rel" "$ROOT/$rel"
  else
    rm -f "$ROOT/$rel"
  fi
done
echo "SBP-035 rollback: PASS"
