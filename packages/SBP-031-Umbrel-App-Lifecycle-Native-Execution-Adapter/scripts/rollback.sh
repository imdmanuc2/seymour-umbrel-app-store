#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

if [[ -z "$BACKUP" && -f "$ROOT/backups/sbp-031-latest" ]]; then
  BACKUP="$(cat "$ROOT/backups/sbp-031-latest")"
fi
[[ -n "$BACKUP" && -d "$BACKUP" ]] || { echo "Invalid SBP-031 backup: ${BACKUP:-<none>}" >&2; exit 1; }

for rel in \
  shared/app_lifecycle/__init__.py \
  shared/app_lifecycle/executor.py \
  shared/contracts/app-lifecycle-execution-v1.json \
  scripts/seymour-app-lifecycle \
  tests/test_sbp031_executor.py \
  tests/test_sbp031_contract.py; do
  rm -rf "$ROOT/$rel"
  if [[ -e "$BACKUP/$rel" ]]; then
    mkdir -p "$ROOT/$(dirname "$rel")"
    cp -a "$BACKUP/$rel" "$ROOT/$rel"
  fi
done

echo "SBP-031 rollback: PASS"
