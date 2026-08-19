#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

COMPOSE="$REPO/seymour-bitcoin-node/docker-compose.yml"
STATUS="$REPO/seymour-bitcoin-node/data/status/app.py"

INSTALLED_COMPOSE="/home/umbrel/umbrel/app-data/seymour-bitcoin-node/docker-compose.yml"
INSTALLED_STATUS="/home/umbrel/umbrel/app-data/seymour-bitcoin-node/data/status/app.py"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-071.2-$STAMP"

"$PKG/scripts/doctor.sh"

mkdir -p "$BACKUP"
cp "$COMPOSE" "$BACKUP/docker-compose.yml.repository"
cp "$STATUS" "$BACKUP/status-app.py.repository"

if sudo test -f "$INSTALLED_COMPOSE"; then
  sudo cp "$INSTALLED_COMPOSE" "$BACKUP/docker-compose.yml.installed"
fi

if sudo test -f "$INSTALLED_STATUS"; then
  sudo cp "$INSTALLED_STATUS" "$BACKUP/status-app.py.installed"
fi

python3 "$PKG/scripts/patch.py" "$COMPOSE" "$STATUS"

python3 -m py_compile "$STATUS"

# Synchronize source into installed app-data, but do not restart or recreate Bitcoin.
if sudo test -f "$INSTALLED_COMPOSE"; then
  sudo cp "$COMPOSE" "$INSTALLED_COMPOSE"
fi

if sudo test -f "$INSTALLED_STATUS"; then
  sudo cp "$STATUS" "$INSTALLED_STATUS"
  sudo python3 -m py_compile "$INSTALLED_STATUS"
fi

REPO_HOOK="$REPO/seymour-bitcoin-node/hooks/pre-install"
INSTALLED_HOOK="/home/umbrel/umbrel/app-data/seymour-bitcoin-node/hooks/pre-install"

if sudo test -f "$INSTALLED_HOOK"; then
  sudo cp "$REPO_HOOK" "$INSTALLED_HOOK"
  sudo chmod +x "$INSTALLED_HOOK"

  sudo env     APP_DATA_DIR="/home/umbrel/umbrel/app-data/seymour-bitcoin-node"     "$INSTALLED_HOOK"
fi

echo "SBP-071.2 runtime identity rematerialization: PASS"
echo "SBP-071.2 source patch: PASS"
echo "SBP-071.2 installed Bitcoin source synchronized: PASS"
echo "Backup: $BACKUP"
echo "SBP-071.2 install: PASS"
echo "No blockchain runtime was stopped, started, restarted, recreated, or uninstalled."
echo "NEXT: run verify.sh, then restart Bitcoin only to activate the Compose healthcheck timeout."
