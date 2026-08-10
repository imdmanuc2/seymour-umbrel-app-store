#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_ID="seymour-blockchain-manager"
SRC="$ROOT/$APP_ID/docker-compose.yml"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID/docker-compose.yml"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$ROOT/backups/sbp-036.3-$STAMP"

"$PKG/scripts/doctor.sh" "$ROOT"

mkdir -p "$BACKUP/repository" "$BACKUP/app-data"
cp -a "$SRC" "$BACKUP/repository/docker-compose.yml"
cp -a "$INSTALLED" "$BACKUP/app-data/docker-compose.yml"

python3 - "$SRC" "$INSTALLED" <<'PY'
from pathlib import Path
import re, sys

for raw in sys.argv[1:]:
    p = Path(raw)
    s = p.read_text()
    original = s

    # Replace exactly the APP_HOST value while preserving indentation.
    s, count = re.subn(
        r'(?m)^(\s*APP_HOST:\s*).+$',
        r'\1web',
        s,
        count=1,
    )
    if count != 1:
        raise SystemExit(f"SBP-036.3 install: could not patch APP_HOST in {p}")

    p.write_text(s)
PY

for f in "$SRC" "$INSTALLED"; do
  grep -Fq 'APP_HOST: web' "$f" || {
    echo "SBP-036.3 install: APP_HOST service alias verification failed: $f"
    exit 1
  }
  if grep -Fq 'APP_HOST: seymour-blockchain-manager_web_1' "$f"; then
    echo "SBP-036.3 install: stale underscore container target remains: $f"
    exit 1
  fi
done

printf '%s\n' "$BACKUP" > "$ROOT/backups/sbp-036.3-latest"

echo "Backup: $BACKUP"
echo "SBP-036.3 repository APP_HOST service alias repair: PASS"
echo "SBP-036.3 installed app-data APP_HOST service alias repair: PASS"
echo "SBP-036.3 install: PASS"
echo "Blockchain Manager restart was NOT performed by install.sh."
echo "No Docker lifecycle command was executed."
echo
echo "NEXT:"
echo "  cd $ROOT"
echo "  ./scripts/seymour-umbrel-app restart seymour-blockchain-manager --execute --confirm RESTART-seymour-blockchain-manager"
echo
echo "Then run:"
echo "  cd $ROOT/packages/SBP-036.3-Blockchain-Manager-App-Proxy-Service-DNS-Repair"
echo "  sudo ./scripts/verify.sh"
