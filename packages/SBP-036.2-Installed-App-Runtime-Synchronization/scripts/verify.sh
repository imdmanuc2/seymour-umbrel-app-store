#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP_ID="seymour-blockchain-manager"
SRC="$ROOT/$APP_ID"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID"
WEB_CONTAINER="seymour-blockchain-manager_web_1"

for x in \
  'SEYMOUR_PLATFORM_ROOT: /seymour-platform' \
  'SEYMOUR_LIFECYCLE_AUDIT_PATH: /evidence/lifecycle-audit.jsonl' \
  'SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH: /evidence/native-app-control' \
  '/home/umbrel/seymour-umbrel-app-store-git/shared:/seymour-platform/shared:ro'
do
  grep -Fq "$x" "$INSTALLED/docker-compose.yml" || {
    echo "SBP-036.2 verify: installed compose missing: $x"
    exit 1
  }
done
echo "SBP-036.2 installed compose verification: PASS"

cmp -s "$SRC/data/web/app.py" "$INSTALLED/data/web/app.py" || {
  echo "SBP-036.2 verify: installed app.py differs from repository"
  exit 1
}
cmp -s "$SRC/data/web/lifecycle_routes.py" "$INSTALLED/data/web/lifecycle_routes.py" || {
  echo "SBP-036.2 verify: installed lifecycle_routes.py differs from repository"
  exit 1
}
echo "SBP-036.2 installed lifecycle HTTP file verification: PASS"

python3 -m py_compile "$INSTALLED/data/web/app.py" "$INSTALLED/data/web/lifecycle_routes.py"

! grep -Eq 'docker[[:space:]].*(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' \
  "$INSTALLED/data/web/lifecycle_routes.py" || {
  echo "SBP-036.2 verify: prohibited Docker lifecycle path found"
  exit 1
}
echo "SBP-036.2 direct Docker lifecycle prohibition: PASS"

command -v docker >/dev/null 2>&1 || {
  echo "SBP-036.2 verify: docker CLI unavailable for read-only runtime inspection"
  exit 2
}

docker inspect "$WEB_CONTAINER" >/dev/null 2>&1 || {
  echo "SBP-036.2 verify: Blockchain Manager web container not found."
  echo "Restart Blockchain Manager through the native Umbrel lifecycle, then rerun verify.sh."
  exit 2
}

RUNNING="$(docker inspect -f '{{.State.Running}}' "$WEB_CONTAINER" 2>/dev/null || true)"
[[ "$RUNNING" == "true" ]] || {
  echo "SBP-036.2 verify: Blockchain Manager web container is not running."
  exit 2
}
echo "SBP-036.2 web container running verification: PASS"

CONFIG_FILES="$(docker inspect "$WEB_CONTAINER" --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}' 2>/dev/null || true)"
printf '%s\n' "$CONFIG_FILES" | grep -Fq '/home/umbrel/umbrel/app-data/seymour-blockchain-manager/docker-compose.yml' || {
  echo "SBP-036.2 verify: running container is not using expected installed app-data compose"
  echo "Config files: $CONFIG_FILES"
  exit 1
}
echo "SBP-036.2 authoritative app-data compose verification: PASS"

MOUNTS="$(docker inspect "$WEB_CONTAINER" --format '{{range .Mounts}}{{println .Source "->" .Destination .Mode}}{{end}}')"
printf '%s\n' "$MOUNTS" | grep -Fq '/home/umbrel/seymour-umbrel-app-store-git/shared -> /seymour-platform/shared ro' || {
  echo "SBP-036.2 verify: running container still lacks /seymour-platform/shared."
  echo "Restart Blockchain Manager through the native Umbrel lifecycle, then rerun verify.sh."
  exit 2
}
echo "SBP-036.2 live shared lifecycle mount verification: PASS"

ENV="$(docker inspect "$WEB_CONTAINER" --format '{{range .Config.Env}}{{println .}}{{end}}')"
for x in \
  'SEYMOUR_PLATFORM_ROOT=/seymour-platform' \
  'SEYMOUR_LIFECYCLE_AUDIT_PATH=/evidence/lifecycle-audit.jsonl' \
  'SEYMOUR_LIFECYCLE_NATIVE_EVIDENCE_PATH=/evidence/native-app-control'
do
  printf '%s\n' "$ENV" | grep -Fq "$x" || {
    echo "SBP-036.2 verify: running container environment missing: $x"
    exit 1
  }
done
echo "SBP-036.2 live lifecycle environment verification: PASS"

docker exec "$WEB_CONTAINER" python - <<'PY'
import os, sys
root = os.environ.get("SEYMOUR_PLATFORM_ROOT")
assert root == "/seymour-platform", root
sys.path.insert(0, root)
from shared.app_lifecycle import LifecycleApiFacade
from shared.umbrel_control import UmbrelAppControlBridge
print("SBP-036.2 live canonical lifecycle imports: PASS")
PY

HISTORY="$(
docker exec "$WEB_CONTAINER" python - <<'PY'
from urllib.request import urlopen
with urlopen("http://127.0.0.1:8080/api/lifecycle/history", timeout=10) as r:
    print(r.status)
    print(r.read().decode())
PY
)"
printf '%s\n' "$HISTORY"
printf '%s\n' "$HISTORY" | head -1 | grep -q '^200$' || {
  echo "SBP-036.2 verify: lifecycle history endpoint did not return HTTP 200"
  exit 1
}
echo "SBP-036.2 live lifecycle history route verification: PASS"

PLAN="$(
docker exec "$WEB_CONTAINER" python - <<'PY'
import json
from urllib.request import Request, urlopen
payload = json.dumps({
    "appId": "seymour-bch-node",
    "action": "restart",
    "execute": False
}).encode()
req = Request(
    "http://127.0.0.1:8080/api/lifecycle/operation",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urlopen(req, timeout=10) as r:
    print(r.status)
    print(r.read().decode())
PY
)"
printf '%s\n' "$PLAN"
printf '%s\n' "$PLAN" | head -1 | grep -q '^200$' || {
  echo "SBP-036.2 verify: lifecycle planning endpoint did not return HTTP 200"
  exit 1
}
printf '%s\n' "$PLAN" | grep -Eq '"executed"[[:space:]]*:[[:space:]]*false' || {
  echo "SBP-036.2 verify: lifecycle planning endpoint did not remain non-executing"
  exit 1
}
echo "SBP-036.2 live lifecycle planning route verification: PASS"

echo
echo "SBP-036.2 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
echo "Docker was used only for read-only inspection and in-container HTTP acceptance checks."
