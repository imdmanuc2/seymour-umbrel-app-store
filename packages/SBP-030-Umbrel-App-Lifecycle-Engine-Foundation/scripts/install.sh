#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-030-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
for rel in   shared/app_lifecycle   shared/contracts/app-lifecycle-v1.json   scripts/seymour-app-lifecycle   tests/test_sbp030_lifecycle_model.py   tests/test_sbp030_contract.py; do
  if [[ -e "$ROOT/$rel" ]]; then
    mkdir -p "$BACKUP/$(dirname "$rel")"
    cp -a "$ROOT/$rel" "$BACKUP/$rel"
  fi
done

cd "$ROOT"
mkdir -p shared/app_lifecycle shared/contracts tests

cp "$PKG/payload/shared/app_lifecycle/__init__.py" shared/app_lifecycle/__init__.py
cp "$PKG/payload/shared/app_lifecycle/model.py" shared/app_lifecycle/model.py
cp "$PKG/payload/shared/app_lifecycle/engine.py" shared/app_lifecycle/engine.py
cp "$PKG/payload/shared/contracts/app-lifecycle-v1.json" shared/contracts/app-lifecycle-v1.json
cp "$PKG/payload/scripts/seymour-app-lifecycle" scripts/seymour-app-lifecycle
chmod +x scripts/seymour-app-lifecycle
cp "$PKG/payload/tests/test_sbp030_lifecycle_model.py" tests/test_sbp030_lifecycle_model.py
cp "$PKG/payload/tests/test_sbp030_contract.py" tests/test_sbp030_contract.py

echo "Backup: $BACKUP"
echo "SBP-030 install: PASS"
echo "No live Umbrel lifecycle action was executed."
