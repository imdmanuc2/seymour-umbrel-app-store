#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-/home/umbrel/seymour-umbrel-app-store-git}"

PYTHONPATH="$ROOT" python3 - <<'TESTPY'
from shared.runtime_state import RuntimeStateService

svc = RuntimeStateService()

def raw(installed=True, running=True, health="healthy",
        reachable=True, healthy=True, ibd=False,
        status="ok", progress=1.0):
    return {
        "installed": installed,
        "running": running,
        "container": {"health": health},
        "rpc": {"probe": {
            "reachable": reachable,
            "healthy": healthy,
            "initialBlockDownload": ibd,
            "status": status,
            "verificationProgress": progress,
        }},
    }

cases = [
    (raw(installed=False, running=False), "offline"),
    (raw(running=False), "stopped"),
    (raw(health="starting", reachable=False, healthy=False), "starting"),
    (raw(ibd=True, progress=0.25), "syncing"),
    (raw(status="rpc-slow", progress=0.5), "syncing"),
    (raw(), "running"),
    (raw(reachable=False, healthy=False), "degraded"),
]
for payload, expected in cases:
    actual = svc.normalize_dict(payload)
    assert actual["state"] == expected, (expected, actual)

print("SBP-038 canonical normalization matrix: PASS")
print("SBP-038 running vocabulary verification: PASS")
TESTPY

grep -Fq 'from shared.runtime_state import' \
  "$ROOT/seymour-blockchain-manager/data/web/runtime_state.py"
grep -Fq 'normalize_runtime_state' \
  "$ROOT/seymour-blockchain-manager/data/web/bch_runtime_probe.py"
grep -Fq 'from bch_runtime_probe import probe as probe_bch_runtime' \
  "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"
grep -Fq 'app_probes={' \
  "$ROOT/seymour-blockchain-manager/data/web/lifecycle_routes.py"

PYTHONPATH="$ROOT" python3 - <<'TESTPY'
from shared.app_lifecycle import AppLifecycleEngine
from shared.app_lifecycle.runtime_state import CanonicalRuntimeStateProvider

def probe():
    return {
        "operationalState": {
            "state": "syncing",
            "reason": "canonical test",
            "rpcReachable": True,
            "rpcHealthy": True,
            "initialBlockDownload": True,
            "verificationProgress": 0.42,
        }
    }

provider = CanonicalRuntimeStateProvider(
    app_urls={},
    app_probes={"seymour-bch-node": probe},
)
state = provider.read_state("seymour-bch-node", AppLifecycleEngine())
assert state is not None
assert state.state == "syncing", state.as_dict()
print("SBP-038 direct lifecycle probe verification: PASS")
TESTPY

! grep -Eq 'docker[[:space:]].*(start|stop|restart|rm|compose[[:space:]]+(up|down|restart))' \
  "$ROOT/shared/runtime_state/service.py" || {
  echo "SBP-038 verify: prohibited Docker lifecycle path found"; exit 1;
}

echo "SBP-038 shared normalization ownership verification: PASS"
echo "SBP-038 direct Docker lifecycle prohibition: PASS"
echo "SBP-038 final verification: PASS"
echo "No live Umbrel lifecycle write action was executed by verify.sh."
