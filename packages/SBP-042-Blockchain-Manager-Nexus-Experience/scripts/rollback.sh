#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
MARKER="$ROOT/backups/sbp-042-latest"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

[[ -f "$MARKER" ]] || {
  echo "SBP-042 rollback: backup marker missing"
  exit 1
}
BACKUP="$(cat "$MARKER")"

for f in app.js index.html style.css; do
  cp -a "$BACKUP/$f" "$WEB/$f"
done

if [[ -d "$INSTALLED" ]]; then
  for f in app.js index.html style.css; do
    cp -a "$WEB/$f" "$INSTALLED/$f"
  done
fi

echo "SBP-042 rollback: Nexus experience assets restored"
echo "SBP-042 rollback: PASS"
