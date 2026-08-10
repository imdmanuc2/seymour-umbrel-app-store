#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-033-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
for rel in \
  shared/app_lifecycle/__init__.py \
  shared/app_lifecycle/audit.py \
  shared/contracts/app-lifecycle-audit-v1.json \
  tests/test_sbp033_audit.py \
  tests/test_sbp033_contract.py; do
  if [[ -e "$ROOT/$rel" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$ROOT/$rel" "$BACKUP/$rel"
  fi
done

mkdir -p "$ROOT/shared/app_lifecycle" "$ROOT/shared/contracts" "$ROOT/tests" "$ROOT/backups"
cp "$PKG/payload/shared/app_lifecycle/__init__.py" "$ROOT/shared/app_lifecycle/__init__.py"
cp "$PKG/payload/shared/app_lifecycle/audit.py" "$ROOT/shared/app_lifecycle/audit.py"
cp "$PKG/payload/shared/contracts/app-lifecycle-audit-v1.json" "$ROOT/shared/contracts/app-lifecycle-audit-v1.json"
cp "$PKG/payload/tests/test_sbp033_audit.py" "$ROOT/tests/test_sbp033_audit.py"
cp "$PKG/payload/tests/test_sbp033_contract.py" "$ROOT/tests/test_sbp033_contract.py"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-033-latest"

echo "Backup: $BACKUP"
echo "SBP-033 install: PASS"
echo "No live Umbrel lifecycle write action was executed."
echo "No runtime audit file was created by install.sh."
