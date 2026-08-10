#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
BACKUP="${2:-}"

if [[ -z "$BACKUP" && -f "$ROOT/backups/sbp-033-latest" ]]; then
  BACKUP="$(cat "$ROOT/backups/sbp-033-latest")"
fi
[[ -n "$BACKUP" && -d "$BACKUP" ]] || { echo "Invalid SBP-033 backup: ${BACKUP:-<none>}" >&2; exit 1; }

for rel in \
  shared/app_lifecycle/__init__.py \
  shared/app_lifecycle/audit.py \
  shared/contracts/app-lifecycle-audit-v1.json \
  tests/test_sbp033_audit.py \
  tests/test_sbp033_contract.py; do
  rm -rf "$ROOT/$rel"
  if [[ -e "$BACKUP/$rel" ]]; then
    mkdir -p "$ROOT/$(dirname "$rel")"
    cp -a "$BACKUP/$rel" "$ROOT/$rel"
  fi
done

echo "SBP-033 rollback: PASS"
echo "Runtime audit history is intentionally preserved."
