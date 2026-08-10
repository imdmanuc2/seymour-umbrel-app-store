#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP="$ROOT/seymour-blockchain-manager/data/web/app.py"
ROUTES="$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"
CONTROL="$ROOT/scripts/seymour-umbrel-app"
SHARED="$ROOT/shared"

for f in "$APP" "$ROUTES" "$COMPOSE" "$CONTROL"; do
  [[ -f "$f" ]] || { echo "SBP-036.1 doctor: missing required file: $f"; exit 1; }
done
[[ -d "$SHARED/app_lifecycle" ]] || { echo "SBP-036.1 doctor: missing shared/app_lifecycle"; exit 1; }
[[ -d "$SHARED/umbrel_control" ]] || { echo "SBP-036.1 doctor: missing shared/umbrel_control"; exit 1; }

python3 -m py_compile "$APP" "$ROUTES"

grep -q 'from lifecycle_routes import LIFECYCLE_HTTP' "$APP" \
  || { echo "SBP-036.1 doctor: SBP-036 lifecycle route import missing"; exit 1; }
grep -q '/api/lifecycle/history' "$APP" \
  || { echo "SBP-036.1 doctor: history route missing"; exit 1; }
grep -q '/api/lifecycle/operation' "$APP" \
  || { echo "SBP-036.1 doctor: operation route missing"; exit 1; }

grep -q 'APP_HOST: seymour-blockchain-manager_web_1' "$COMPOSE" \
  || { echo "SBP-036.1 doctor: app_proxy host anchor missing"; exit 1; }
grep -q 'APP_PORT: 8080' "$COMPOSE" \
  || { echo "SBP-036.1 doctor: app_proxy port anchor missing"; exit 1; }
grep -q '/home/umbrel/seymour-umbrel-app-store-git/scripts:/control:ro' "$COMPOSE" \
  || { echo "SBP-036.1 doctor: control mount anchor missing"; exit 1; }

if grep -q 'SEYMOUR_PLATFORM_ROOT: /seymour-platform' "$COMPOSE" &&
   grep -q '/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro' "$COMPOSE"; then
  echo "SBP-036.1 doctor: runtime wiring already present"
else
  echo "SBP-036.1 doctor: runtime wiring repair required"
fi

echo "SBP-036.1 doctor: Blockchain Manager HTTP/runtime anchors PASS"
echo "SBP-036.1 doctor: PASS"
