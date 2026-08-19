#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

LATEST="$(
  find "$REPO/backups" \
    -maxdepth 1 \
    -type d \
    -name 'sbp-071.2-*' \
    | sort \
    | tail -1
)"

test -n "$LATEST" || {
  echo "ERROR: no SBP-071.2 backup found"
  exit 1
}

COMPOSE="$REPO/seymour-bitcoin-node/docker-compose.yml"
STATUS="$REPO/seymour-bitcoin-node/data/status/app.py"

INSTALLED_COMPOSE="/home/umbrel/umbrel/app-data/seymour-bitcoin-node/docker-compose.yml"
INSTALLED_STATUS="/home/umbrel/umbrel/app-data/seymour-bitcoin-node/data/status/app.py"

cp "$LATEST/docker-compose.yml.repository" "$COMPOSE"
cp "$LATEST/status-app.py.repository" "$STATUS"

if [[ -f "$LATEST/docker-compose.yml.installed" ]]; then
  sudo cp "$LATEST/docker-compose.yml.installed" "$INSTALLED_COMPOSE"
fi

if [[ -f "$LATEST/status-app.py.installed" ]]; then
  sudo cp "$LATEST/status-app.py.installed" "$INSTALLED_STATUS"
fi

echo "SBP-071.2 rollback: PASS"
echo "No blockchain runtime was restarted."
