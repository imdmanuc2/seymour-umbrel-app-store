#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
LATEST="$ROOT/backups/sbp-034-latest"
[[ -f "$LATEST" ]] || { echo "SBP-034 rollback: no backup marker found" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
[[ -d "$BACKUP" ]] || { echo "SBP-034 rollback: backup missing: $BACKUP" >&2; exit 1; }
for rel in \
  shared/app_lifecycle/__init__.py \
  shared/app_lifecycle/operations.py \
  shared/contracts/app-lifecycle-operation-v1.json \
  tests/test_sbp034_operations.py \
  tests/test_sbp034_contract.py; do
  if [[ -e "$BACKUP/$rel" ]]; then
    mkdir -p "$ROOT/$(dirname "$rel")"
    cp -a "$BACKUP/$rel" "$ROOT/$rel"
  else
    rm -f "$ROOT/$rel"
  fi
done
echo "SBP-034 rollback: PASS"
