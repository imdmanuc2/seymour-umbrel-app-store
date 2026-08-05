#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$REPO/backups/sbp-003-$STAMP"

"$ROOT/scripts/doctor.sh" "$REPO"

mkdir -p "$BACKUP"
cp -a \
  "$REPO/seymour-bch-node" \
  "$BACKUP/"

cp -a \
  "$ROOT/payload/seymour-bch-node/." \
  "$REPO/seymour-bch-node/"

mkdir -p "$REPO/docs"
cp -a \
  "$ROOT/payload/docs/." \
  "$REPO/docs/"

python3 -m py_compile \
  "$REPO/seymour-bch-node/data/status/app.py" \
  "$REPO/seymour-bch-node/data/status/provisioning.py"

echo "Backup: $BACKUP"
echo "SBP-003 install: PASS"
echo "No Umbrel app, container, blockchain sync, RPC exposure, firewall, or host changes were performed."
