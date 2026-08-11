#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"

fail() {
  echo "SBP-046 verify: FAIL: $*"
  exit 1
}
pass() {
  echo "SBP-046 $*: PASS"
}

echo "===== 1. UMBREL APP STATE ====="
STATE_JSON="$("$ROOT/scripts/seymour-umbrel-app" state seymour-blockchain-manager)"
printf '%s\n' "$STATE_JSON"
printf '%s\n' "$STATE_JSON" | grep -Fq '"success": true' || fail "Blockchain Manager Umbrel state failed"
printf '%s\n' "$STATE_JSON" | grep -Fq '"state": "ready"' || fail "Blockchain Manager is not ready"
pass "Umbrel manager state"

echo
echo "===== 2. BCH CONTAINERS ====="
NODE_ID="$(
  sudo docker ps -q \
    --filter 'label=com.docker.compose.project=seymour-bch-node' \
    --filter 'label=com.docker.compose.service=node' \
    | head -1
)"
STATUS_ID="$(
  sudo docker ps -q \
    --filter 'label=com.docker.compose.project=seymour-bch-node' \
    --filter 'label=com.docker.compose.service=status' \
    | head -1
)"
[[ -n "$NODE_ID" ]] || fail "BCH node container not found"
[[ -n "$STATUS_ID" ]] || fail "BCH status container not found"

NODE_HEALTH="$(sudo docker inspect "$NODE_ID" --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}')"
printf 'Node health: %s\n' "$NODE_HEALTH"
[[ "$NODE_HEALTH" == "healthy" || "$NODE_HEALTH" == "running" ]] || fail "BCH node container unhealthy"
pass "BCH container health"

echo
echo "===== 3. DIRECT BCH RPC ====="
RPC_JSON="$(
  sudo docker exec -i "$NODE_ID" \
    bitcoin-cli -conf=/generated/bitcoin.conf getblockchaininfo
)"
NETWORK_JSON="$(
  sudo docker exec -i "$NODE_ID" \
    bitcoin-cli -conf=/generated/bitcoin.conf getnetworkinfo
)"
printf '%s\n' "$RPC_JSON"
printf '%s\n' "$NETWORK_JSON"

python3 - <<'PY' "$RPC_JSON" "$NETWORK_JSON"
import json,sys
chain=json.loads(sys.argv[1])
network=json.loads(sys.argv[2])
required=("blocks","headers","verificationprogress","initialblockdownload")
missing=[k for k in required if k not in chain]
assert not missing, missing
assert chain.get("chain") == "main", chain
assert isinstance(chain["blocks"], int)
assert isinstance(chain["headers"], int)
assert 0 <= float(chain["verificationprogress"]) <= 1
assert isinstance(chain["initialblockdownload"], bool)
assert bool(network.get("networkactive")) is True
print("Direct RPC contract valid")
PY
pass "direct BCH RPC contract"

echo
echo "===== 4. STATUS SERVICE ====="
STATUS_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
from urllib.request import urlopen
with urlopen("http://status:8080/api/status", timeout=10) as r:
    print(r.read().decode())
PY
)"
HEALTH_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
from urllib.request import urlopen
with urlopen("http://status:8080/api/health", timeout=10) as r:
    print(r.read().decode())
PY
)"
printf '%s\n' "$STATUS_JSON"
printf '%s\n' "$HEALTH_JSON"

python3 - <<'PY' "$RPC_JSON" "$STATUS_JSON" "$HEALTH_JSON"
import json,sys
rpc=json.loads(sys.argv[1])
status=json.loads(sys.argv[2])
health=json.loads(sys.argv[3])

assert status.get("healthy") is True, status
assert status.get("rpcReachable") is True, status
assert status.get("blocks") == rpc.get("blocks"), (status,rpc)
assert status.get("headers") == rpc.get("headers"), (status,rpc)

vp=float(status.get("verificationProgress"))
direct=float(rpc.get("verificationprogress"))
assert abs(vp-direct) < 0.01, (vp,direct)

assert status.get("initialBlockDownload") == rpc.get("initialblockdownload"), (status,rpc)
assert health.get("healthy") is True, health
assert health.get("rpcReachable") is True, health

print("Status service matches direct RPC for core sync fields")
PY
pass "status service consistency"

echo
echo "===== 5. CANONICAL RUNTIME PROBE ====="
RUNTIME_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
import json
from bch_runtime_probe import probe
print(json.dumps(probe()))
PY
)"
printf '%s\n' "$RUNTIME_JSON"

python3 - <<'PY' "$RUNTIME_JSON" "$RPC_JSON"
import json,sys
runtime=json.loads(sys.argv[1])
rpc=json.loads(sys.argv[2])
op=runtime.get("operationalState") or {}

assert op.get("state") in {
    "starting","syncing","running","degraded","stopped","offline","error","unknown"
}, op
assert op.get("rpcReachable") is True, op
assert op.get("rpcHealthy") is True, op

probe=((runtime.get("rpc") or {}).get("probe") or {})
if rpc.get("initialblockdownload"):
    assert op.get("state") == "syncing", op
assert probe.get("height") == rpc.get("blocks"), (probe,rpc)
assert probe.get("headers") == rpc.get("headers"), (probe,rpc)

print("Canonical runtime probe matches direct RPC")
PY
pass "canonical runtime state"

echo
echo "===== 6. DASHBOARD CONTRACT ====="
DASHBOARD_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
import json
import telemetry
print(json.dumps(telemetry.dashboard_payload()))
PY
)"
printf '%s\n' "$DASHBOARD_JSON"

python3 - <<'PY' "$DASHBOARD_JSON"
import json,sys
payload=json.loads(sys.argv[1])
text=json.dumps(payload)
assert "bitcoin-cash-mainnet" in text, payload
assert "runtimeState" in text, payload
assert "runtimeRpcHealthy" in text, payload
assert "operationalState" in text, payload
print("Dashboard contains canonical BCH runtime projection")
PY
pass "Blockchain Manager dashboard contract"

echo
echo "===== 7. OPERATIONS DIAGNOSTICS ====="
DIAG_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
import json
from operations_center import diagnostics
r=diagnostics()
print(json.dumps({
    "status": getattr(r.status, "value", str(r.status)),
    "result": r.result,
    "error": r.error,
}))
PY
)"
printf '%s\n' "$DIAG_JSON"

python3 - <<'PY' "$DIAG_JSON"
import json,sys
payload=json.loads(sys.argv[1])
assert payload.get("error") in (None,""), payload
result=payload.get("result") or {}
checks=result.get("checks") or []
assert len(checks) >= 3, result
assert any(c.get("name") == "rpc-reachable" for c in checks), checks
print("Structured diagnostics checks present")
PY
pass "Operations diagnostics"

echo
echo "===== 8. OPERATIONS LOGS ====="
LOG_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
import json
from operations_center import recent_logs
r=recent_logs(50)
print(json.dumps({
    "status": getattr(r.status, "value", str(r.status)),
    "result": r.result,
    "error": r.error,
}))
PY
)"
printf '%s\n' "$LOG_JSON" | head -c 6000
echo

python3 - <<'PY' "$LOG_JSON"
import json,sys
payload=json.loads(sys.argv[1])
result=payload.get("result") or {}
assert result.get("source") == "docker-engine-api", result
assert result.get("success") is True, result
assert isinstance(result.get("stdout"), str), result
print("Operations logs available through Docker Engine API")
PY
pass "Operations logs"

echo
echo "===== 9. LIFECYCLE PLANNING ====="
PLAN_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError

body=json.dumps({
    "appId":"seymour-bch-node",
    "action":"restart",
    "execute":False
}).encode()

req=Request(
    "http://127.0.0.1:8080/api/lifecycle/operation",
    data=body,
    headers={"Content-Type":"application/json"},
    method="POST",
)

try:
    with urlopen(req, timeout=30) as r:
        print(r.read().decode())
except HTTPError as e:
    print(e.read().decode())
PY
)"
printf '%s\n' "$PLAN_JSON"

python3 - <<'PY' "$PLAN_JSON"
import json,sys
payload=json.loads(sys.argv[1])
assert payload.get("executed") is False, payload
assert payload.get("appId") == "seymour-bch-node", payload
assert payload.get("action") == "restart", payload
assert payload.get("lifecycleState") in {
    "starting","syncing","running","degraded","stopped","offline","error","unknown"
}, payload
if payload.get("allowed") is True:
    assert payload.get("confirmationRequired") is True, payload
    assert payload.get("confirmationToken"), payload
print("Lifecycle planning contract valid")
PY
pass "lifecycle planning"

echo
echo "===== 10. LIFECYCLE HISTORY ====="
HISTORY_JSON="$(
  sudo docker exec -i seymour-blockchain-manager-web-1 \
    python - <<'PY'
from urllib.request import urlopen
with urlopen(
    "http://127.0.0.1:8080/api/lifecycle/history?appId=seymour-bch-node",
    timeout=15
) as r:
    print(r.read().decode())
PY
)"
printf '%s\n' "$HISTORY_JSON"

python3 - <<'PY' "$HISTORY_JSON"
import json,sys
payload=json.loads(sys.argv[1])
assert payload.get("contract") == "seymour.lifecycle-api-history", payload
assert isinstance(payload.get("items"), list), payload
print(f"Lifecycle history items: {len(payload.get('items') or [])}")
PY
pass "lifecycle history/audit"

echo
echo "===== 11. NEXUS PROJECTION ANCHORS ====="
grep -Fq 'runtimeState' "$WEB/nexus_integration.py" || fail "Nexus runtimeState projection anchor missing"
grep -Fq 'runtimeRpcHealthy' "$WEB/nexus_integration.py" || fail "Nexus runtimeRpcHealthy projection anchor missing"
grep -Fq 'runtimeVerificationProgress' "$WEB/nexus_integration.py" || fail "Nexus verification progress projection anchor missing"
pass "Nexus runtime projection anchors"

echo
echo "===== 12. FRONTEND CONTRACT ====="
grep -Fq 'function presentedRuntime(provider)' "$WEB/app.js" || fail "presentedRuntime missing"
grep -Fq 'function hasCompleteSyncTelemetry(telemetry)' "$WEB/app.js" || fail "sync telemetry continuity guard missing"
grep -Fq 'RUNTIME_PRESENTATION_GRACE_MS' "$WEB/app.js" || fail "runtime stabilization missing"
grep -Fq 'function renderRuntimeFocus()' "$WEB/app.js" || fail "runtime focus missing"
grep -Fq 'function renderOperationalSummary()' "$WEB/app.js" || fail "operational summary missing"
grep -Fq 'async function showOperationsCenter(providerId)' "$WEB/app.js" || fail "Operations Center missing"
pass "frontend runtime/operations contract"

echo
echo "===== 13. NO DUPLICATE STATE INFERENCE ====="
if grep -Fq 'lifecycle = "not-installed"' "$WEB/telemetry.py"; then
  fail "legacy dashboard lifecycle inference remains"
fi
grep -Fq 'runtime = probe_bch_runtime()' "$WEB/telemetry.py" || fail "dashboard not using canonical BCH probe"
pass "single runtime-state ownership"

echo
echo "===== 14. NO DIRECT DOCKER LIFECYCLE ====="
if grep -ERn \
  'docker[[:space:]]+(start|stop|restart|rm)|docker[[:space:]]+compose[[:space:]]+(up|down|restart)' \
  "$ROOT/shared" \
  "$WEB" \
  "$ROOT/scripts" \
  --exclude='*.before-*' \
  --exclude='*.backup' \
  --exclude='*.md' \
  2>/dev/null; then
  fail "direct Docker lifecycle command found"
fi
pass "direct Docker lifecycle prohibition"

echo
echo "===== 15. FREEZE SUMMARY ====="
cat <<'SUMMARY'
BCH Version 1 acceptance criteria satisfied.

Reference provider baseline:
  Provider: Bitcoin Cash
  Runtime: Bitcoin Cash Node
  Canonical state: shared runtime-state model
  Lifecycle: native Umbrel guarded lifecycle
  Dashboard: canonical runtime projection
  Operations: diagnostics/logs/planning/history
  Nexus: runtime state projected
  Frontend: stabilized canonical runtime presentation

No live lifecycle write was executed by SBP-046 verify.sh.
SUMMARY

echo
echo "SBP-046 final verification: PASS"
