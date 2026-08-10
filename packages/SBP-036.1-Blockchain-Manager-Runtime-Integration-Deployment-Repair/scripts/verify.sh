#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP="$ROOT/seymour-blockchain-manager/data/web/app.py"
ROUTES="$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"

python3 -m py_compile "$APP" "$ROUTES"

for x in \
  'SEYMOUR_PLATFORM_ROOT: /seymour-platform' \
  'SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl' \
  'SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control' \
  '/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro'
do
  grep -q "$x" "$COMPOSE" || { echo "SBP-036.1 verify: compose wiring missing: $x"; exit 1; }
done
echo "SBP-036.1 static compose wiring verification: PASS"

# Safety: runtime routes may invoke only the canonical lifecycle facade.
! grep -Eq 'docker[[:space:]].*(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' "$ROUTES" \
  || { echo "SBP-036.1 verify: prohibited Docker lifecycle path found"; exit 1; }
echo "SBP-036.1 direct Docker lifecycle prohibition: PASS"

if ! command -v docker >/dev/null 2>&1; then
  echo "SBP-036.1 verify: docker CLI unavailable for read-only runtime inspection"
  exit 2
fi

WEB_CONTAINER="seymour-blockchain-manager_web_1"
if ! docker inspect "$WEB_CONTAINER" >/dev/null 2>&1; then
  echo "SBP-036.1 verify: Blockchain Manager web container not found."
  echo "Restart Blockchain Manager through Umbrel, then rerun verify.sh."
  exit 2
fi

RUNNING="$(docker inspect -f '{{.State.Running}}' "$WEB_CONTAINER" 2>/dev/null || true)"
if [[ "$RUNNING" != "true" ]]; then
  echo "SBP-036.1 verify: Blockchain Manager web container is not running."
  echo "Restart Blockchain Manager through Umbrel, then rerun verify.sh."
  exit 2
fi
echo "SBP-036.1 web container running verification: PASS"

docker inspect "$WEB_CONTAINER" --format '{{range .Mounts}}{{println .Source "->" .Destination .Mode}}{{end}}' \
  | grep -F -- '/home/umbrel/seymour-umbrel-app-store-git/shared -> /seymour-platform/shared ro' >/dev/null \
  || {
    echo "SBP-036.1 verify: running container does not have the shared lifecycle mount."
    echo "The compose file is repaired but the container still needs a native Umbrel restart."
    exit 2
  }
echo "SBP-036.1 live shared mount verification: PASS"

docker exec "$WEB_CONTAINER" python - <<'PY'
import os, sys
assert os.environ.get("SEYMOUR_PLATFORM_ROOT") == "/seymour-platform"
sys.path.insert(0, "/seymour-platform")
from shared.app_lifecycle import LifecycleApiFacade
from shared.umbrel_control import UmbrelAppControlBridge
print("SBP-036.1 live canonical lifecycle imports: PASS")
PY

# Use Python inside the web container so verification does not depend on wget/curl packages.
HISTORY="$(
docker exec "$WEB_CONTAINER" python - <<'PY'
from urllib.request import urlopen
with urlopen("http://127.0.0.1:8080/api/lifecycle/history", timeout=10) as r:
    print(r.status)
    print(r.read().decode())
PY
)"
printf '%s\n' "$HISTORY"
printf '%s\n' "$HISTORY" | head -1 | grep -q '^200$' \
  || { echo "SBP-036.1 verify: lifecycle history route did not return HTTP 200"; exit 1; }
echo "SBP-036.1 live lifecycle history route verification: PASS"

PLAN="$(
docker exec "$WEB_CONTAINER" python - <<'PY'
import json
from urllib.request import Request, urlopen
payload=json.dumps({
    "appId":"seymour-bch-node",
    "action":"restart",
    "execute":False
}).encode()
req=Request(
    "http://127.0.0.1:8080/api/lifecycle/operation",
    data=payload,
    headers={"Content-Type":"application/json"},
    method="POST",
)
with urlopen(req, timeout=10) as r:
    print(r.status)
    print(r.read().decode())
PY
)"
printf '%s\n' "$PLAN"
printf '%s\n' "$PLAN" | head -1 | grep -q '^200$' \
  || { echo "SBP-036.1 verify: lifecycle planning route did not return HTTP 200"; exit 1; }
printf '%s\n' "$PLAN" | grep -q '"executed": false' \
  || { echo "SBP-036.1 verify: planning response did not remain non-executing"; exit 1; }
echo "SBP-036.1 live lifecycle planning route verification: PASS"

echo
echo "SBP-036.1 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
echo "docker was used for read-only inspection/exec only; no Docker lifecycle command was used."
