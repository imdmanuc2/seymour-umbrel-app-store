#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"
WEB="$ROOT/seymour-blockchain-manager/data/web"
TELEMETRY="$WEB/telemetry.py"
PROBE="$WEB/bch_runtime_probe.py"
COMPOSE="$ROOT/seymour-blockchain-manager/docker-compose.yml"
python3 -m py_compile "$TELEMETRY" "$PROBE"
grep -Fq 'from bch_runtime_probe import probe as probe_bch_runtime' "$TELEMETRY"
grep -Fq 'runtime = probe_bch_runtime()' "$TELEMETRY"
grep -Fq '"runtimeState": runtime_state' "$TELEMETRY"
grep -Fq '"runtimeRpcReachable": rpc_reachable' "$TELEMETRY"
grep -Fq '"runtimeRpcHealthy": rpc_healthy' "$TELEMETRY"
grep -Fq '"progressPercent": progress' "$TELEMETRY"
grep -Fq '"peers": rpc_probe.get("peers")' "$TELEMETRY"
if grep -Fq 'lifecycle = "not-installed"' "$TELEMETRY"; then
  echo "SBP-040 verify: duplicate legacy lifecycle calculation remains"; exit 1
fi
echo "SBP-040 duplicate dashboard state inference prohibition: PASS"
for f in "$TELEMETRY" "$PROBE" "$COMPOSE"; do
  if grep -Fq 'seymour-bch-node_status_1:8080' "$f"; then
    echo "SBP-040 verify: stale generated BCH status hostname remains in $f"; exit 1
  fi
done
grep -Fq 'http://status:8080/api/status' "$COMPOSE"
echo "SBP-040 stable BCH status DNS verification: PASS"
PYTHONPATH="$WEB:$ROOT" python3 - <<'TESTPY'
import telemetry
sample_runtime = {
    "appId": "seymour-bch-node",
    "installed": True,
    "running": True,
    "lifecycleStatus": "syncing",
    "container": {"found": True, "running": True, "health": "healthy"},
    "operationalState": {
        "state": "syncing",
        "reason": "Runtime RPC is healthy and initial block download is active.",
        "rpcReachable": True,
        "rpcHealthy": True,
        "initialBlockDownload": True,
        "verificationProgress": 0.0467,
    },
    "rpc": {
        "probe": {
            "reachable": True,
            "healthy": True,
            "height": 241604,
            "headers": 963539,
            "peers": 8,
            "progressPercent": 4.67,
            "initialBlockDownload": True,
        },
        "status": {"payload": {"storage": {"usedBytes": 10162376595}}},
    },
}
original = telemetry.probe_bch_runtime
try:
    telemetry.probe_bch_runtime = lambda: sample_runtime
    result = telemetry.bch_telemetry()
finally:
    telemetry.probe_bch_runtime = original
assert result["runtimeState"] == "syncing", result
assert result["lifecycleStatus"] == "syncing", result
assert result["installed"] is True, result
assert result["rpc"]["reachable"] is True, result
assert result["rpc"]["healthy"] is True, result
assert result["sync"]["height"] == 241604, result
assert result["sync"]["headers"] == 963539, result
assert result["sync"]["progressPercent"] == 4.67, result
assert result["peers"] == 8, result
print("SBP-040 canonical dashboard sample projection: PASS")
TESTPY
! grep -Eq 'docker[[:space:]].*(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' "$TELEMETRY" "$PROBE" || {
  echo "SBP-040 verify: prohibited Docker lifecycle command found"; exit 1;
}
echo "SBP-040 live runtime status contract verification: PASS"
echo "SBP-040 direct Docker lifecycle prohibition: PASS"
echo "SBP-040 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
