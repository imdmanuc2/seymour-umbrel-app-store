#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
LATEST="$ROOT/backups/sbp-036-latest"
[[ -f "$LATEST" ]] || { echo "SBP-036 rollback: no backup pointer found" >&2; exit 1; }
BACKUP="$(cat "$LATEST")"
[[ -d "$BACKUP" ]] || { echo "SBP-036 rollback: backup directory missing: $BACKUP" >&2; exit 1; }
for rel in \
  seymour-blockchain-manager/data/web/app.py \
  seymour-blockchain-manager/data/web/lifecycle_routes.py \
  seymour-blockchain-manager/docker-compose.yml \
  tests/test_sbp036_http.py; do
  if [[ -e "$BACKUP/$rel" ]]; then
    mkdir -p "$ROOT/$(dirname "$rel")"
    cp -a "$BACKUP/$rel" "$ROOT/$rel"
  else
    rm -f "$ROOT/$rel"
  fi
done
echo "SBP-036 rollback: PASS"
echo "Blockchain Manager restart was NOT performed by rollback.sh."
