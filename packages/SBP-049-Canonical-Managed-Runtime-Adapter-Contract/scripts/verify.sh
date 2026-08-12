#!/usr/bin/env bash
set -euo pipefail
PKG="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT="$(cd "$PKG/../.." && pwd)"
cd "$ROOT"

python3 -m py_compile shared/managed_runtime/*.py

python3 - <<'PY'
import json
from pathlib import Path
c=json.loads(Path("shared/contracts/managed-runtime-adapter-v1.json").read_text())
assert c["contract"]=="seymour.managed-runtime"
assert c["version"]=="1.0"
assert c["directDockerLifecycle"] is False
assert c["duplicateLifecycleExecutionPath"] is False
l=json.loads(Path("shared/contracts/app-lifecycle-v1.json").read_text())
assert "syncing" in l["states"] and "offline" in l["states"]
PY

python3 - <<'PY'
from shared.managed_runtime import ManagedRuntimeAdapterRegistry, UmbrelManagedRuntimeAdapter

class FakeRuntime:
    def installed(self, app_id): return app_id=="demo-node"
    def source_available(self, app_id): return True
    def inspect_app(self, app_id):
        return {
            "app_id":app_id,"installed":True,"source_available":True,"version":"1.2.3",
            "lifecycle_status":"running",
            "containers":[{"name":"demo","service":"node","status":"Up","running":True,
                           "healthy":True,"image":"demo:1.2.3","started_at":None}],
            "dependencies":[],"missing_dependencies":[],"health":{"status":"healthy"},
            "paths":{},"errors":[]
        }
    def collect_logs(self, app_id, tail=200): return {"tail":tail}

def probe():
    return {"operationalState":{
        "state":"syncing","rpcReachable":True,"rpcHealthy":True,"rpcStatus":"ok",
        "initialBlockDownload":True,"verificationProgress":0.42
    }}

a=UmbrelManagedRuntimeAdapter(FakeRuntime(), state_probes={"demo-node":probe})
r=ManagedRuntimeAdapterRegistry(); r.register(a)
p=r.resolve("umbrel").inspect("demo-node", provider_id="bitcoin-mainnet").to_dict()
assert p["contract"]=="seymour.managed-runtime"
assert p["state"]["state"]=="syncing"
assert p["state"]["rpcReachable"] is True
assert p["state"]["initialBlockDownload"] is True
assert p["capabilities"]["restart"] is True
try:
    a.lifecycle("demo-node","restart")
except NotImplementedError:
    pass
else:
    raise AssertionError("duplicate lifecycle execution path")
PY

if grep -RniE 'docker[[:space:]]+(start|stop|restart|rm)|subprocess.*docker|os\.system.*docker' shared/managed_runtime; then
  echo "SBP-049 verify: direct Docker lifecycle pattern detected" >&2
  exit 1
fi

echo "SBP-049 canonical managed runtime contract verification: PASS"
echo "SBP-049 adapter registry verification: PASS"
echo "SBP-049 Umbrel adapter projection verification: PASS"
echo "SBP-049 canonical runtime-state delegation verification: PASS"
echo "SBP-049 lifecycle contract reconciliation verification: PASS"
echo "SBP-049 duplicate lifecycle execution prohibition: PASS"
echo "SBP-049 direct Docker lifecycle prohibition: PASS"
echo "SBP-049 final verification: PASS"
echo "No live lifecycle write or blockchain configuration action was executed by verify.sh."
