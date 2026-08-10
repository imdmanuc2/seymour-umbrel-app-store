#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ID="seymour-blockchain-manager"
SRC="$ROOT/$APP_ID"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-036.2-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP/data/web"
cp -a "$INSTALLED/docker-compose.yml" "$BACKUP/docker-compose.yml"

[[ -f "$INSTALLED/data/web/app.py" ]] && cp -a "$INSTALLED/data/web/app.py" "$BACKUP/data/web/app.py"
[[ -f "$INSTALLED/data/web/lifecycle_routes.py" ]] && cp -a "$INSTALLED/data/web/lifecycle_routes.py" "$BACKUP/data/web/lifecycle_routes.py"

cp -a "$SRC/docker-compose.yml" "$INSTALLED/docker-compose.yml"
mkdir -p "$INSTALLED/data/web"
cp -a "$SRC/data/web/app.py" "$INSTALLED/data/web/app.py"
cp -a "$SRC/data/web/lifecycle_routes.py" "$INSTALLED/data/web/lifecycle_routes.py"

python3 -m py_compile "$INSTALLED/data/web/app.py" "$INSTALLED/data/web/lifecycle_routes.py"

for x in \
  'SEYMOUR_PLATFORM_ROOT: /seymour-platform' \
  'SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl' \
  'SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control' \
  '/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro'
do
  grep -Fq "$x" "$INSTALLED/docker-compose.yml" || {
    echo "SBP-036.2 install: installed compose synchronization failed: $x"
    exit 1
  }
done

cmp -s "$SRC/data/web/app.py" "$INSTALLED/data/web/app.py" || {
  echo "SBP-036.2 install: installed app.py does not match repository"
  exit 1
}
cmp -s "$SRC/data/web/lifecycle_routes.py" "$INSTALLED/data/web/lifecycle_routes.py" || {
  echo "SBP-036.2 install: installed lifecycle_routes.py does not match repository"
  exit 1
}

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-036.2-latest"

echo "Backup: $BACKUP"
echo "SBP-036.2 installed compose synchronization: PASS"
echo "SBP-036.2 installed lifecycle HTTP file synchronization: PASS"
echo "SBP-036.2 install: PASS"
echo "Blockchain Manager restart was NOT performed by install.sh."
echo "No live Umbrel lifecycle write action was executed."
echo
echo "NEXT:"
echo "  cd $ROOT"
echo "  ./scripts/seymour-umbrel-app restart seymour-blockchain-manager --execute --confirm RESTART-seymour-blockchain-manager"
echo
echo "Then:"
echo "  cd $ROOT/packages/SBP-036.2-Installed-App-Runtime-Synchronization"
echo "  sudo ./scripts/verify.sh"
