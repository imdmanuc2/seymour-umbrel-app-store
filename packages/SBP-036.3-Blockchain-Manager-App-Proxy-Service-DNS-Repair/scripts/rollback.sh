#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP_ID="seymour-blockchain-manager"
MARKER="$ROOT/backups/sbp-036.3-latest"
SRC="$ROOT/$APP_ID/docker-compose.yml"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID/docker-compose.yml"

[[ -f "$MARKER" ]] || { echo "SBP-036.3 rollback: backup marker missing"; exit 1; }
BACKUP="$(cat "$MARKER")"

[[ -f "$BACKUP/repository/docker-compose.yml" ]] || {
  echo "SBP-036.3 rollback: repository backup missing"
  exit 1
}
[[ -f "$BACKUP/app-data/docker-compose.yml" ]] || {
  echo "SBP-036.3 rollback: app-data backup missing"
  exit 1
}

cp -a "$BACKUP/repository/docker-compose.yml" "$SRC"
cp -a "$BACKUP/app-data/docker-compose.yml" "$INSTALLED"

echo "SBP-036.3 rollback: repository and installed compose restored"
echo "Blockchain Manager restart was NOT performed by rollback.sh."
echo "SBP-036.3 rollback: PASS"
