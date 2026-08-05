#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-004-$STAMP"

"$ROOT/scripts/doctor.sh" "$REPO"

mkdir -p "$BACKUP"

for name in shared scripts docs; do
  if [[ -e "$REPO/$name" ]]; then
    cp -a "$REPO/$name" "$BACKUP/"
  fi
done

mkdir -p \
  "$REPO/shared" \
  "$REPO/scripts" \
  "$REPO/docs"

cp -a \
  "$ROOT/payload/shared/." \
  "$REPO/shared/"

cp -a \
  "$ROOT/payload/scripts/." \
  "$REPO/scripts/"

cp -a \
  "$ROOT/payload/docs/." \
  "$REPO/docs/"

chmod +x \
  "$REPO/scripts/seymour-umbrel-runtime"

python3 -m py_compile \
  "$REPO/shared/umbrel_runtime/models.py" \
  "$REPO/shared/umbrel_runtime/runtime.py" \
  "$REPO/shared/umbrel_runtime/cli.py"

echo "Backup: $BACKUP"
echo "SBP-004 install: PASS"
echo "No app, container, blockchain, service, firewall, or host changes were performed."
