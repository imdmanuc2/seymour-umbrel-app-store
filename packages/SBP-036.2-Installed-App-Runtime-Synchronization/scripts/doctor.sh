#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP_ID="seymour-blockchain-manager"
SRC="$ROOT/$APP_ID"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID"

for p in \
  "$SRC/docker-compose.yml" \
  "$SRC/data/web/app.py" \
  "$SRC/data/web/lifecycle_routes.py" \
  "$ROOT/scripts/seymour-umbrel-app"
do
  [[ -e "$p" ]] || { echo "SBP-036.2 doctor: missing required source: $p"; exit 1; }
done

[[ -d "$ROOT/shared/app_lifecycle" ]] || { echo "SBP-036.2 doctor: missing shared/app_lifecycle"; exit 1; }
[[ -d "$ROOT/shared/umbrel_control" ]] || { echo "SBP-036.2 doctor: missing shared/umbrel_control"; exit 1; }
[[ -d "$INSTALLED" ]] || { echo "SBP-036.2 doctor: installed app-data directory not found: $INSTALLED"; exit 1; }
[[ -f "$INSTALLED/docker-compose.yml" ]] || { echo "SBP-036.2 doctor: installed compose file missing"; exit 1; }

python3 -m py_compile "$SRC/data/web/app.py" "$SRC/data/web/lifecycle_routes.py"

for x in \
  'SEYMOUR_PLATFORM_ROOT: /seymour-platform' \
  'SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl' \
  'SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control' \
  '/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro'
do
  grep -Fq "$x" "$SRC/docker-compose.yml" || {
    echo "SBP-036.2 doctor: repository compose missing expected wiring: $x"
    exit 1
  }
done

grep -Fq 'from lifecycle_routes import LIFECYCLE_HTTP' "$SRC/data/web/app.py" || {
  echo "SBP-036.2 doctor: repository app.py missing lifecycle HTTP import"
  exit 1
}
grep -Fq '/api/lifecycle/history' "$SRC/data/web/app.py" || {
  echo "SBP-036.2 doctor: repository app.py missing lifecycle history route"
  exit 1
}
grep -Fq '/api/lifecycle/operation' "$SRC/data/web/app.py" || {
  echo "SBP-036.2 doctor: repository app.py missing lifecycle operation route"
  exit 1
}

echo "SBP-036.2 doctor: repository canonical runtime definition PASS"
echo "SBP-036.2 doctor: installed app-data target detected PASS"
echo "SBP-036.2 doctor: PASS"
