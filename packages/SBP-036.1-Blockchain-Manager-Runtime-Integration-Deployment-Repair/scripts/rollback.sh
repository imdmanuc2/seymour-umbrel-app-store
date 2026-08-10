#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-036.1-latest"

[[ -f "$MARKER" ]] || { echo "SBP-036.1 rollback: no backup marker found"; exit 1; }
BACKUP="$(cat "$MARKER")"
SRC="$BACKUP/seymour-blockchain-manager/docker-compose.yml"
DST="$ROOT/seymour-blockchain-manager/docker-compose.yml"
[[ -f "$SRC" ]] || { echo "SBP-036.1 rollback: backup compose missing: $SRC"; exit 1; }

cp -a "$SRC" "$DST"
echo "SBP-036.1 rollback: restored $DST"
echo "Blockchain Manager restart was NOT performed by rollback.sh."
echo "Restart through the native Umbrel lifecycle after rollback if the running container must be reconciled."
echo "SBP-036.1 rollback: PASS"
