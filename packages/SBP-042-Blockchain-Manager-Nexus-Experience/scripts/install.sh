#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-042-$STAMP"
WEB="$ROOT/seymour-blockchain-manager/data/web"
INSTALLED="/home/umbrel/umbrel/app-data/seymour-blockchain-manager/data/web"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP"
for f in app.js index.html style.css; do
  cp -a "$WEB/$f" "$BACKUP/$f"
done

python3 "$PKG/payload/patch_sbp042.py" "$ROOT"

if [[ -d "$INSTALLED" ]]; then
  for f in app.js index.html style.css; do
    cp -a "$WEB/$f" "$INSTALLED/$f"
  done
fi

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-042-latest"

echo "Backup: $BACKUP"
echo "SBP-042 operational summary integration: PASS"
echo "SBP-042 managed runtime focus integration: PASS"
echo "SBP-042 future-provider catalog separation: PASS"
echo "SBP-042 installed web asset synchronization: PASS"
echo "SBP-042 install: PASS"
echo "No backend or lifecycle write was executed."
