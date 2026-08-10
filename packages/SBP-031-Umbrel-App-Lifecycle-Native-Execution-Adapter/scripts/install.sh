#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-031-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
for rel in \
  shared/app_lifecycle/__init__.py \
  shared/app_lifecycle/executor.py \
  shared/contracts/app-lifecycle-execution-v1.json \
  scripts/seymour-app-lifecycle \
  tests/test_sbp031_executor.py \
  tests/test_sbp031_contract.py; do
  if [[ -e "$ROOT/$rel" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$ROOT/$rel" "$BACKUP/$rel"
  fi
done

mkdir -p "$ROOT/shared/app_lifecycle" "$ROOT/shared/contracts" "$ROOT/scripts" "$ROOT/tests"
cp "$PKG/payload/shared/app_lifecycle/__init__.py" "$ROOT/shared/app_lifecycle/__init__.py"
cp "$PKG/payload/shared/app_lifecycle/executor.py" "$ROOT/shared/app_lifecycle/executor.py"
cp "$PKG/payload/shared/contracts/app-lifecycle-execution-v1.json" "$ROOT/shared/contracts/app-lifecycle-execution-v1.json"
cp "$PKG/payload/scripts/seymour-app-lifecycle" "$ROOT/scripts/seymour-app-lifecycle"
chmod +x "$ROOT/scripts/seymour-app-lifecycle"
cp "$PKG/payload/tests/test_sbp031_executor.py" "$ROOT/tests/test_sbp031_executor.py"
cp "$PKG/payload/tests/test_sbp031_contract.py" "$ROOT/tests/test_sbp031_contract.py"

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-031-latest"

echo "Backup: $BACKUP"
echo "SBP-031 install: PASS"
echo "No live Umbrel lifecycle write action was executed."
