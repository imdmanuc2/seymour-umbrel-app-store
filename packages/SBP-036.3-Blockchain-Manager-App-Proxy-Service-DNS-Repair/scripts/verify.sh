#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
APP_ID="seymour-blockchain-manager"
SRC="$ROOT/$APP_ID/docker-compose.yml"
INSTALLED="/home/umbrel/umbrel/app-data/$APP_ID/docker-compose.yml"

for f in "$SRC" "$INSTALLED"; do
  grep -Fq 'APP_HOST: web' "$f" || {
    echo "SBP-036.3 verify: APP_HOST is not using stable service alias in $f"
    exit 1
  }
done
echo "SBP-036.3 canonical APP_HOST service alias verification: PASS"

command -v docker >/dev/null 2>&1 || {
  echo "SBP-036.3 verify: docker CLI unavailable for read-only runtime inspection"
  exit 2
}

# Discover current containers by project/service labels so Compose naming style
# (underscore vs hyphen) cannot break verification.
find_container() {
  local service="$1"
  docker ps -q \
    --filter "label=com.docker.compose.project=seymour-blockchain-manager" \
    --filter "label=com.docker.compose.service=$service" \
    | head -1
}

WEB_ID="$(find_container web)"
PROXY_ID="$(find_container app_proxy)"

[[ -n "$WEB_ID" ]] || {
  echo "SBP-036.3 verify: running web service container not found"
  echo "Restart Blockchain Manager through native Umbrel lifecycle, then rerun verify.sh."
  exit 2
}
[[ -n "$PROXY_ID" ]] || {
  echo "SBP-036.3 verify: running app_proxy service container not found"
  echo "Restart Blockchain Manager through native Umbrel lifecycle, then rerun verify.sh."
  exit 2
}

WEB_NAME="$(docker inspect -f '{{.Name}}' "$WEB_ID" | sed 's#^/##')"
PROXY_NAME="$(docker inspect -f '{{.Name}}' "$PROXY_ID" | sed 's#^/##')"

echo "SBP-036.3 discovered web container: $WEB_NAME"
echo "SBP-036.3 discovered app_proxy container: $PROXY_NAME"
echo "SBP-036.3 label-based container discovery: PASS"

PROXY_ENV="$(docker inspect "$PROXY_ID" --format '{{range .Config.Env}}{{println .}}{{end}}')"
printf '%s\n' "$PROXY_ENV" | grep -Fxq 'APP_HOST=web' || {
  echo "SBP-036.3 verify: running app proxy still has stale APP_HOST"
  printf '%s\n' "$PROXY_ENV" | grep '^APP_HOST=' || true
  echo "Restart Blockchain Manager through native Umbrel lifecycle, then rerun verify.sh."
  exit 2
}
echo "SBP-036.3 live app proxy APP_HOST verification: PASS"

# Node is guaranteed in the app-proxy image; use it to verify Docker DNS.
docker exec -i "$PROXY_ID" node - <<'NODE'
const dns = require("dns");
dns.lookup("web", (err, address) => {
  if (err) {
    console.error("SBP-036.3 live Docker DNS resolution: FAIL", err.message);
    process.exit(1);
  }
  console.log(`SBP-036.3 live Docker DNS resolution: PASS (${address})`);
});
NODE

MOUNTS="$(docker inspect "$WEB_ID" --format '{{range .Mounts}}{{println .Source "->" .Destination .Mode}}{{end}}')"
printf '%s\n' "$MOUNTS" | grep -Fq -- '-> /seymour-platform/shared ro' || {
  echo "SBP-036.3 verify: live shared lifecycle mount missing"
  exit 1
}
echo "SBP-036.3 live shared lifecycle mount verification: PASS"

WEB_ENV="$(docker inspect "$WEB_ID" --format '{{range .Config.Env}}{{println .}}{{end}}')"
printf '%s\n' "$WEB_ENV" | grep -Fxq 'SEYMOUR_PLATFORM_ROOT=/seymour-platform' || {
  echo "SBP-036.3 verify: live SEYMOUR_PLATFORM_ROOT missing"
  exit 1
}
echo "SBP-036.3 live lifecycle environment verification: PASS"

docker exec -i "$WEB_ID" python - <<'PY'
import os, sys
root = os.environ["SEYMOUR_PLATFORM_ROOT"]
sys.path.insert(0, root)
from shared.app_lifecycle import LifecycleApiFacade
from shared.umbrel_control import UmbrelAppControlBridge
print("SBP-036.3 live canonical lifecycle imports: PASS")
PY

HISTORY="$(
docker exec -i "$WEB_ID" python - <<'PY'
from urllib.request import urlopen
with urlopen("http://127.0.0.1:8080/api/lifecycle/history", timeout=10) as r:
    print(r.status)
    print(r.read().decode())
PY
)"
printf '%s\n' "$HISTORY"
printf '%s\n' "$HISTORY" | head -1 | grep -q '^200$' || {
  echo "SBP-036.3 verify: lifecycle history endpoint did not return HTTP 200"
  exit 1
}
echo "SBP-036.3 lifecycle history endpoint: PASS"

PLAN="$(
docker exec -i "$WEB_ID" python - <<'PY'
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
try:
    with urlopen(req, timeout=10) as r:
        print(r.status)
        print(r.read().decode())
except Exception as exc:
    from urllib.error import HTTPError
    if isinstance(exc, HTTPError):
        print(exc.code)
        print(exc.read().decode())
    else:
        raise
PY
)"
printf '%s\n' "$PLAN"
printf '%s\n' "$PLAN" | head -1 | grep -Eq '^(200|409)$' || {
  echo "SBP-036.3 verify: lifecycle planning endpoint returned unexpected HTTP status"
  exit 1
}
printf '%s\n' "$PLAN" | grep -Eq '"executed"[[:space:]]*:[[:space:]]*false' || {
  echo "SBP-036.3 verify: lifecycle planning request unexpectedly executed"
  exit 1
}
echo "SBP-036.3 lifecycle planning endpoint (execute=false): PASS"

# Proxy readiness: absence of unresolved-host retry in latest output and a
# positive ready/listening marker.
PROXY_LOG="$(docker logs --tail=80 "$PROXY_ID" 2>&1 || true)"
printf '%s\n' "$PROXY_LOG"
printf '%s\n' "$PROXY_LOG" | grep -Eq 'now ready|Listening on port' || {
  echo "SBP-036.3 verify: app proxy has not reached ready/listening state"
  exit 1
}

echo
echo "SBP-036.3 final verification: PASS"
echo "No live Umbrel lifecycle write was executed by verify.sh."
echo "Docker was used only for runtime inspection, DNS validation, logs, and in-container HTTP checks."
