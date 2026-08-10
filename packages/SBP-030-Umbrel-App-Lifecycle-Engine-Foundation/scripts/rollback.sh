#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

[[ -d "$BACKUP" ]] || { echo "Invalid SBP-030 backup: $BACKUP" >&2; exit 1; }

for rel in   shared/app_lifecycle   shared/contracts/app-lifecycle-v1.json   scripts/seymour-app-lifecycle   tests/test_sbp030_lifecycle_model.py   tests/test_sbp030_contract.py; do
  rm -rf "$ROOT/$rel"
  if [[ -e "$BACKUP/$rel" ]]; then
    mkdir -p "$ROOT/$(dirname "$rel")"
    cp -a "$BACKUP/$rel" "$ROOT/$rel"
  fi
done

echo "SBP-030 rollback: PASS"
