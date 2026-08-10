#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP_ID="seymour-blockchain-manager"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID"
MARKER="$ROOT/backups/sbp-036.2-latest"

[[ -f "$MARKER" ]] || { echo "SBP-036.2 rollback: no backup marker found"; exit 1; }
BACKUP="$(cat "$MARKER")"
[[ -d "$BACKUP" ]] || { echo "SBP-036.2 rollback: backup directory missing: $BACKUP"; exit 1; }

cp -a "$BACKUP/docker-compose.yml" "$INSTALLED/docker-compose.yml"

if [[ -f "$BACKUP/data/web/app.py" ]]; then
  cp -a "$BACKUP/data/web/app.py" "$INSTALLED/data/web/app.py"
fi

if [[ -f "$BACKUP/data/web/lifecycle_routes.py" ]]; then
  cp -a "$BACKUP/data/web/lifecycle_routes.py" "$INSTALLED/data/web/lifecycle_routes.py"
else
  rm -f "$INSTALLED/data/web/lifecycle_routes.py"
fi

echo "SBP-036.2 rollback: installed runtime files restored from $BACKUP"
echo "Blockchain Manager restart was NOT performed by rollback.sh."
echo "Restart through the native Umbrel lifecycle if the running container must be reconciled."
echo "SBP-036.2 rollback: PASS"
