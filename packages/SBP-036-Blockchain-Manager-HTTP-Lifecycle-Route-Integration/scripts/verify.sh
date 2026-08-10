#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP="$ROOT/seymour-blockchain-manager/data/web/app.py"
ROUTES="$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"
TEST="$ROOT/tests/test_sbp036_http.py"

python3 -m py_compile "$APP" "$ROUTES" "$TEST"
python3 "$TEST"

grep -q 'from lifecycle_routes import LIFECYCLE_HTTP' "$APP"
grep -q 'self.path.startswith("/api/lifecycle/history")' "$APP"
grep -q 'self.path == "/api/lifecycle/operation"' "$APP"
grep -q 'LIFECYCLE_HTTP.legacy_operation(action, body)' "$APP"
grep -q 'SEYMOUR_PLATFORM_ROOT: /seymour-platform' "$COMPOSE"
grep -q '/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro' "$COMPOSE"

# Safety boundaries: the HTTP integration must not contain Docker lifecycle execution.
if grep -Eiq 'docker[[:space:]]+(start|stop|restart|rm|run|compose[[:space:]]+(up|down|restart))' "$ROUTES"; then
  echo "SBP-036 verify: direct Docker lifecycle implementation detected" >&2
  exit 1
fi
if grep -Eq 'subprocess\.(run|Popen)|os\.system' "$ROUTES"; then
  echo "SBP-036 verify: HTTP layer contains a second command execution path" >&2
  exit 1
fi

echo "SBP-036 canonical HTTP lifecycle routes verification: PASS"
echo "SBP-036 legacy lifecycle compatibility route verification: PASS"
echo "SBP-036 shared lifecycle mount verification: PASS"
echo "SBP-036 duplicate execution path prohibition: PASS"
echo "SBP-036 direct Docker lifecycle prohibition: PASS"
echo "SBP-036 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
echo "A Blockchain Manager restart is required before the new container mount/routes become live."
