#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-034-$STAMP"
"$PKG/scripts/doctor.sh" "$ROOT"
mkdir -p "$BACKUP"
for rel in \
  shared/app_lifecycle/__init__.py \
  shared/app_lifecycle/operations.py \
  shared/contracts/app-lifecycle-operation-v1.json \
  tests/test_sbp034_operations.py \
  tests/test_sbp034_contract.py; do
  if [[ -e "$ROOT/$rel" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$ROOT/$rel" "$BACKUP/$rel"
  fi
done
mkdir -p "$ROOT/shared/app_lifecycle" "$ROOT/shared/contracts" "$ROOT/tests" "$ROOT/backups"
cp "$PKG/payload/shared/app_lifecycle/__init__.py" "$ROOT/shared/app_lifecycle/__init__.py"
cp "$PKG/payload/shared/app_lifecycle/operations.py" "$ROOT/shared/app_lifecycle/operations.py"
cp "$PKG/payload/shared/contracts/app-lifecycle-operation-v1.json" "$ROOT/shared/contracts/app-lifecycle-operation-v1.json"
cp "$PKG/payload/tests/test_sbp034_operations.py" "$ROOT/tests/test_sbp034_operations.py"
cp "$PKG/payload/tests/test_sbp034_contract.py" "$ROOT/tests/test_sbp034_contract.py"
printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-034-latest"
echo "Backup: $BACKUP"
echo "SBP-034 install: PASS"
echo "No live Umbrel lifecycle write action was executed."
